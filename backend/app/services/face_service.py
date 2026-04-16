"""
Face service — face registration, matching, and gallery retrieval.

Handles the business logic for:
- Registering a child's reference face
- Retrieving a child's photo gallery (parent view)
- Managing unmatched faces (teacher/admin view)
"""

import uuid
from datetime import datetime

from sqlalchemy import select, func, update, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.face import Face, ChildReferenceFace
from ..models.photo import Photo
from ..models.child import Child, parent_children
from ..utils.s3 import S3Client
from ..config import get_settings


class FaceService:
    def __init__(self, db: AsyncSession, storage: S3Client):
        self.db = db
        self.storage = storage
        self.settings = get_settings()

    async def verify_parent_child(self, parent_id: uuid.UUID, child_id: uuid.UUID) -> bool:
        """Verify that a parent-child relationship exists."""
        result = await self.db.execute(
            select(parent_children).where(
                parent_children.c.parent_id == parent_id,
                parent_children.c.child_id == child_id,
            )
        )
        return result.first() is not None

    async def get_child_gallery(
        self,
        child_id: uuid.UUID,
        parent_id: uuid.UUID,
        page: int = 1,
        limit: int = 20,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> dict:
        """
        Get a timeline gallery of photos containing a specific child.

        Only accessible to parents of that child. Photos are grouped by day.

        Raises:
            PermissionError: If parent doesn't own this child.
        """
        # Verify relationship
        if not await self.verify_parent_child(parent_id, child_id):
            raise PermissionError("Access denied: not parent of this child")

        # Fetch child info
        child_result = await self.db.execute(select(Child).where(Child.id == child_id))
        child = child_result.scalar_one_or_none()
        if not child:
            raise ValueError("Child not found")

        # Build query: photos containing this child's face
        query = (
            select(Photo)
            .join(Face, Face.photo_id == Photo.id)
            .where(Face.child_id == child_id)
            .where(Photo.status == "ready")
        )

        if date_from:
            query = query.where(func.date(Photo.captured_at) >= date_from)
        if date_to:
            query = query.where(func.date(Photo.captured_at) <= date_to)

        # Count total
        count_q = select(func.count(func.distinct(Photo.id))).select_from(query.subquery())
        total = (await self.db.execute(count_q)).scalar() or 0

        # Paginate
        query = query.distinct().order_by(Photo.captured_at.desc())
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.db.execute(query)
        photos = result.scalars().all()

        # Group by date and generate signed URLs
        timeline: dict[str, list] = {}
        for photo in photos:
            date_key = (photo.captured_at or photo.created_at).strftime("%Y-%m-%d")
            if date_key not in timeline:
                timeline[date_key] = []

            image_url = await self.storage.get_signed_url(photo.s3_key, expires=3600)
            thumb_url = None
            if photo.s3_thumbnail_key:
                thumb_url = await self.storage.get_signed_url(photo.s3_thumbnail_key, expires=3600)

            timeline[date_key].append({
                "id": photo.id,
                "image_url": image_url,
                "thumbnail_url": thumb_url or image_url,
                "status": photo.status,
                "face_count": photo.face_count,
                "captured_at": photo.captured_at,
                "created_at": photo.created_at,
            })

        timeline_list = [
            {"date": date, "photos": items}
            for date, items in sorted(timeline.items(), reverse=True)
        ]

        return {
            "child": {"id": child.id, "full_name": child.full_name},
            "timeline": timeline_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": max(1, (total + limit - 1) // limit),
            },
        }

    async def register_reference_face(
        self,
        child_id: uuid.UUID,
        embedding: list[float],
        crop_key: str | None = None,
    ) -> dict:
        """
        Save a reference face embedding for a child and retroactively
        match existing unmatched faces.

        Returns:
            Dict with reference face info and matched photo count.
        """
        # Save reference
        ref = ChildReferenceFace(
            child_id=child_id,
            embedding=embedding,
            s3_crop_key=crop_key,
            is_primary=True,
        )
        self.db.add(ref)
        await self.db.commit()
        await self.db.refresh(ref)

        # Get child's playgroup
        child_result = await self.db.execute(select(Child).where(Child.id == child_id))
        child = child_result.scalar_one_or_none()

        # Retroactive matching: find unmatched faces in the same playgroup
        matched_count = 0
        if child:
            threshold = self.settings.face_match_threshold
            match_result = await self.db.execute(text("""
                UPDATE faces
                SET child_id = :child_id,
                    match_status = 'matched',
                    match_distance = sub.distance
                FROM (
                    SELECT f.id, f.embedding <=> :embedding AS distance
                    FROM faces f
                    JOIN photos p ON f.photo_id = p.id
                    WHERE f.match_status = 'unmatched'
                      AND p.playgroup_id = :playgroup_id
                      AND f.embedding <=> :embedding < :threshold
                ) sub
                WHERE faces.id = sub.id
            """), {
                "child_id": str(child_id),
                "embedding": str(embedding),
                "playgroup_id": str(child.playgroup_id),
                "threshold": threshold,
            })
            matched_count = match_result.rowcount  # type: ignore
            await self.db.commit()

        crop_url = None
        if crop_key:
            crop_url = await self.storage.get_signed_url(crop_key, expires=3600)

        return {
            "child_id": child_id,
            "reference_face_id": ref.id,
            "crop_url": crop_url,
            "matched_photos_count": matched_count,
        }

    async def get_unmatched_faces(
        self,
        playgroup_id: uuid.UUID,
        page: int = 1,
        limit: int = 50,
    ) -> list[dict]:
        """Get all unmatched faces in a playgroup for manual review."""
        query = (
            select(Face)
            .join(Photo, Face.photo_id == Photo.id)
            .where(Face.match_status == "unmatched")
            .where(Photo.playgroup_id == playgroup_id)
            .order_by(Face.created_at.desc())
            .offset((page - 1) * limit)
            .limit(limit)
        )

        result = await self.db.execute(query)
        faces = result.scalars().all()

        items = []
        for face in faces:
            crop_url = None
            if face.s3_crop_key:
                crop_url = await self.storage.get_signed_url(face.s3_crop_key, expires=3600)

            items.append({
                "id": face.id,
                "photo_id": face.photo_id,
                "crop_url": crop_url,
                "confidence": face.confidence,
                "match_status": face.match_status,
                "child_id": face.child_id,
                "created_at": face.created_at,
            })

        return items

    async def assign_face_to_child(
        self,
        face_id: uuid.UUID,
        child_id: uuid.UUID,
    ) -> dict:
        """Manually assign a face to a child (teacher/admin action)."""
        result = await self.db.execute(select(Face).where(Face.id == face_id))
        face = result.scalar_one_or_none()

        if not face:
            raise ValueError("Face not found")

        face.child_id = child_id
        face.match_status = "matched"
        await self.db.commit()

        return {
            "face_id": face.id,
            "child_id": child_id,
            "match_status": "matched",
        }
