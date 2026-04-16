"""
Face processing Celery task.

Runs asynchronously after a photo is uploaded:
1. Downloads image from S3
2. Detects faces (RetinaFace)
3. Generates 512-dim embeddings (ArcFace)
4. Matches against known children (pgvector cosine similarity)
5. Saves face records to PostgreSQL
"""

import io
import uuid
import logging

from sqlalchemy import text

from . import celery_app
from ..database import SyncSessionFactory
from ..models.photo import Photo
from ..models.face import Face
from ..utils.face_engine import FaceEngine
from ..utils.s3 import get_s3_client
from ..config import get_settings

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def process_photo_faces(self, photo_id: str):
    """
    Detect faces in an uploaded photo and match them to known children.

    This task is idempotent — safe to retry on failure.
    """
    settings = get_settings()
    db = SyncSessionFactory()
    s3 = get_s3_client()

    try:
        # 1. Fetch photo record
        photo = db.query(Photo).filter(Photo.id == uuid.UUID(photo_id)).first()
        if not photo:
            logger.error(f"Photo {photo_id} not found")
            return {"status": "error", "message": "Photo not found"}

        if photo.status == "ready":
            logger.info(f"Photo {photo_id} already processed, skipping")
            return {"status": "skipped"}

        # 2. Download image from S3
        logger.info(f"Processing photo {photo_id} (key: {photo.s3_key})")
        image_bytes = s3.download(photo.s3_key)

        # 3. Detect faces and generate embeddings
        engine = FaceEngine()
        faces = engine.detect_and_embed(
            image_bytes,
            min_confidence=settings.face_min_confidence,
            min_face_size=settings.face_min_size,
        )

        if not faces:
            photo.status = "ready"
            photo.face_count = 0
            db.commit()
            logger.info(f"Photo {photo_id}: no faces detected")
            return {"status": "ok", "faces_found": 0}

        # 4. Process each detected face
        matched_children = set()

        for face_data in faces:
            face_id = uuid.uuid4()

            # Save face crop to S3
            crop_key = None
            try:
                crop_buffer = io.BytesIO()
                face_data["crop"].save(crop_buffer, format="JPEG", quality=85)
                crop_key = f"faces/{photo.playgroup_id}/{photo_id}/{face_id}.jpg"
                s3.upload_sync(
                    key=crop_key,
                    data=crop_buffer.getvalue(),
                    content_type="image/jpeg",
                )
            except Exception as e:
                logger.warning(f"Failed to save face crop: {e}")

            # Convert embedding to list for pgvector
            embedding_list = face_data["embedding"].tolist()

            # 5. Similarity search against known children in this playgroup
            child_id = None
            match_status = "unmatched"
            match_distance = None

            try:
                match_result = db.execute(text("""
                    SELECT child_id, embedding <=> :embedding AS distance
                    FROM child_reference_faces
                    WHERE child_id IN (
                        SELECT id FROM children WHERE playgroup_id = :playgroup_id
                    )
                    ORDER BY embedding <=> :embedding
                    LIMIT 1
                """), {
                    "embedding": str(embedding_list),
                    "playgroup_id": str(photo.playgroup_id),
                }).first()

                if match_result and match_result.distance < settings.face_match_threshold:
                    child_id = match_result.child_id
                    match_status = "matched"
                    match_distance = float(match_result.distance)
                    matched_children.add(child_id)
                    logger.info(
                        f"Face matched to child {child_id} "
                        f"(distance: {match_distance:.4f})"
                    )
            except Exception as e:
                logger.warning(f"Similarity search failed: {e}")

            # 6. Save face record
            bbox = face_data["bbox"]
            face_record = Face(
                id=face_id,
                photo_id=uuid.UUID(photo_id),
                child_id=child_id,
                bbox_x=int(bbox[0]),
                bbox_y=int(bbox[1]),
                bbox_w=int(bbox[2] - bbox[0]),
                bbox_h=int(bbox[3] - bbox[1]),
                confidence=face_data["confidence"],
                embedding=embedding_list,
                s3_crop_key=crop_key,
                match_status=match_status,
                match_distance=match_distance,
            )
            db.add(face_record)

        # 7. Update photo status
        photo.status = "ready"
        photo.face_count = len(faces)
        db.commit()

        result = {
            "status": "ok",
            "faces_found": len(faces),
            "matched": len(matched_children),
        }
        logger.info(f"Photo {photo_id} processed: {result}")
        return result

    except Exception as exc:
        db.rollback()
        # Mark as failed after all retries exhausted
        try:
            photo = db.query(Photo).filter(Photo.id == uuid.UUID(photo_id)).first()
            if photo and self.request.retries >= self.max_retries:
                photo.status = "failed"
                db.commit()
        except Exception:
            pass
        logger.error(f"Face processing failed for {photo_id}: {exc}", exc_info=True)
        raise self.retry(exc=exc)

    finally:
        db.close()
