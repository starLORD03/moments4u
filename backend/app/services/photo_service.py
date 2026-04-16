"""
Photo service — upload, listing, and deletion business logic.
"""

import uuid
from datetime import datetime, timedelta, timezone

from fastapi import UploadFile
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.photo import Photo
from ..utils.s3 import S3Client
from ..config import get_settings

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/heic", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


class PhotoService:
    def __init__(self, db: AsyncSession, storage: S3Client):
        self.db = db
        self.storage = storage
        self.settings = get_settings()

    async def upload_batch(
        self,
        files: list[UploadFile],
        playgroup_id: uuid.UUID,
        uploaded_by: uuid.UUID,
    ) -> dict:
        """
        Upload a batch of photos to S3 and save metadata.

        Each photo is assigned a UUID key, stored privately, and queued
        for face processing via Celery.

        Returns:
            dict with 'uploaded' and 'failed' lists.
        """
        uploaded = []
        failed = []

        for file in files:
            try:
                # Validate MIME type
                if file.content_type not in ALLOWED_TYPES:
                    failed.append({
                        "filename": file.filename or "unknown",
                        "error": f"Unsupported type: {file.content_type}",
                    })
                    continue

                # Read content
                content = await file.read()

                # Validate size
                if len(content) > MAX_FILE_SIZE:
                    failed.append({
                        "filename": file.filename or "unknown",
                        "error": f"File too large: {len(content)} bytes (max {MAX_FILE_SIZE})",
                    })
                    continue

                # Generate obfuscated S3 key
                photo_id = uuid.uuid4()
                now = datetime.now(timezone.utc)
                s3_key = f"{playgroup_id}/{now.year}/{now.month:02d}/{photo_id}.enc"

                # Upload to S3
                await self.storage.upload(
                    key=s3_key,
                    data=content,
                    content_type=file.content_type or "image/jpeg",
                )

                # Calculate expiry
                expires_at = now + timedelta(days=self.settings.photo_retention_days)

                # Save metadata
                photo = Photo(
                    id=photo_id,
                    s3_key=s3_key,
                    original_filename=file.filename,
                    mime_type=file.content_type or "image/jpeg",
                    file_size_bytes=len(content),
                    status="processing",
                    playgroup_id=playgroup_id,
                    uploaded_by=uploaded_by,
                    captured_at=now,
                    expires_at=expires_at,
                )
                self.db.add(photo)

                # Queue face processing (import here to avoid circular deps)
                from ..tasks.face_processing import process_photo_faces
                process_photo_faces.delay(str(photo_id))

                # Generate signed thumbnail URL
                thumbnail_url = await self.storage.get_signed_url(s3_key, expires=3600)

                uploaded.append({
                    "id": photo_id,
                    "thumbnail_url": thumbnail_url,
                    "status": "processing",
                    "created_at": now,
                })

            except Exception as e:
                failed.append({
                    "filename": file.filename or "unknown",
                    "error": str(e),
                })

        await self.db.commit()
        return {"uploaded": uploaded, "failed": failed}

    async def get_teacher_uploads(
        self,
        teacher_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        date_filter: str | None = None,
    ) -> dict:
        """Get paginated list of photos uploaded by a teacher."""
        query = select(Photo).where(Photo.uploaded_by == teacher_id)

        if date_filter:
            query = query.where(func.date(Photo.created_at) == date_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Paginate
        query = query.order_by(Photo.created_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        photos = result.scalars().all()

        # Generate signed URLs
        photo_items = []
        for photo in photos:
            thumbnail_url = None
            key = photo.s3_thumbnail_key or photo.s3_key
            if key:
                thumbnail_url = await self.storage.get_signed_url(key, expires=3600)

            photo_items.append({
                "id": photo.id,
                "thumbnail_url": thumbnail_url,
                "status": photo.status,
                "face_count": photo.face_count,
                "captured_at": photo.captured_at,
                "created_at": photo.created_at,
            })

        return {
            "photos": photo_items,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": max(1, (total + limit - 1) // limit),
            },
        }

    async def delete_photo(self, photo_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a photo if the user is the uploader."""
        result = await self.db.execute(
            select(Photo).where(Photo.id == photo_id, Photo.uploaded_by == user_id)
        )
        photo = result.scalar_one_or_none()
        if not photo:
            return False

        # Delete from S3
        self.storage.delete(photo.s3_key)  # type: ignore
        if photo.s3_thumbnail_key:
            self.storage.delete(photo.s3_thumbnail_key)  # type: ignore

        # Delete from DB (faces cascade)
        await self.db.execute(delete(Photo).where(Photo.id == photo_id))
        await self.db.commit()
        return True
