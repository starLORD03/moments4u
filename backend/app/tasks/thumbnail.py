"""
Thumbnail generation Celery task.

Creates a resized thumbnail for uploaded photos.
"""

import io
import uuid
import logging

from PIL import Image

from . import celery_app
from ..database import SyncSessionFactory
from ..models.photo import Photo
from ..utils.s3 import get_s3_client

logger = logging.getLogger(__name__)

THUMBNAIL_SIZE = (400, 400)


@celery_app.task(bind=True, max_retries=2)
def generate_thumbnail(self, photo_id: str):
    """Generate a thumbnail for an uploaded photo."""
    db = SyncSessionFactory()
    s3 = get_s3_client()

    try:
        photo = db.query(Photo).filter(Photo.id == uuid.UUID(photo_id)).first()
        if not photo:
            return {"status": "error", "message": "Photo not found"}

        if photo.s3_thumbnail_key:
            return {"status": "skipped", "message": "Thumbnail already exists"}

        # Download original
        image_bytes = s3.download(photo.s3_key)

        # Create thumbnail
        img = Image.open(io.BytesIO(image_bytes))

        # Store original dimensions
        photo.width = img.width
        photo.height = img.height

        # Resize maintaining aspect ratio
        img.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)

        # Save to buffer
        thumb_buffer = io.BytesIO()
        img.save(thumb_buffer, format="JPEG", quality=80, optimize=True)

        # Upload thumbnail
        thumb_key = photo.s3_key.replace(".enc", "_thumb.jpg")
        s3.upload_sync(
            key=thumb_key,
            data=thumb_buffer.getvalue(),
            content_type="image/jpeg",
        )

        photo.s3_thumbnail_key = thumb_key
        db.commit()

        logger.info(f"Thumbnail generated for {photo_id}")
        return {"status": "ok", "thumbnail_key": thumb_key}

    except Exception as exc:
        db.rollback()
        logger.error(f"Thumbnail generation failed: {exc}")
        raise self.retry(exc=exc)

    finally:
        db.close()
