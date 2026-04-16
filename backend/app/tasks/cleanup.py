"""
Photo cleanup Celery task.

Runs daily via Celery Beat to delete expired photos from S3 and PostgreSQL.
Deletion order: S3 objects → PostgreSQL records (faces cascade).
"""

import logging
from datetime import datetime, timezone

from sqlalchemy import select, delete

from . import celery_app
from ..database import SyncSessionFactory
from ..models.photo import Photo
from ..models.face import Face
from ..models.audit import AuditLog
from ..utils.s3 import get_s3_client

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=2, default_retry_delay=300)
def cleanup_expired_photos(self):
    """
    Delete all photos past their expiry date.

    This task is idempotent and safe to re-run.

    Deletion order:
    1. Collect S3 keys (originals, thumbnails, face crops)
    2. Batch delete from S3
    3. Delete from PostgreSQL (faces cascade automatically)
    4. Write audit log entry
    """
    db = SyncSessionFactory()
    s3 = get_s3_client()
    now = datetime.now(timezone.utc)

    try:
        # 1. Find expired photos
        expired_photos = db.execute(
            select(Photo).where(Photo.expires_at <= now)
        ).scalars().all()

        if not expired_photos:
            logger.info("Cleanup: no expired photos found")
            return {"status": "ok", "deleted": 0}

        # 2. Collect all S3 keys
        s3_keys = []
        photo_ids = []

        for photo in expired_photos:
            photo_ids.append(photo.id)
            s3_keys.append(photo.s3_key)

            if photo.s3_thumbnail_key:
                s3_keys.append(photo.s3_thumbnail_key)

        # Get face crop keys
        face_crops = db.execute(
            select(Face.s3_crop_key).where(
                Face.photo_id.in_(photo_ids),
                Face.s3_crop_key.isnot(None),
            )
        ).scalars().all()
        s3_keys.extend(face_crops)

        # 3. Batch delete from S3
        deleted_s3 = 0
        for i in range(0, len(s3_keys), 1000):
            batch = s3_keys[i : i + 1000]
            try:
                s3.delete_batch(batch)
                deleted_s3 += len(batch)
            except Exception as e:
                logger.error(f"S3 batch delete failed: {e}")

        # 4. Delete from PostgreSQL (faces CASCADE)
        db.execute(delete(Photo).where(Photo.id.in_(photo_ids)))

        # 5. Audit log
        db.add(AuditLog(
            action="system.cleanup",
            resource_type="photo",
            metadata_={
                "photos_deleted": len(photo_ids),
                "s3_objects_deleted": deleted_s3,
                "timestamp": now.isoformat(),
            },
        ))

        db.commit()

        result = {
            "status": "ok",
            "photos_deleted": len(photo_ids),
            "s3_objects_deleted": deleted_s3,
        }
        logger.info(f"Cleanup complete: {result}")
        return result

    except Exception as exc:
        db.rollback()
        logger.error(f"Cleanup failed: {exc}", exc_info=True)
        raise self.retry(exc=exc)

    finally:
        db.close()
