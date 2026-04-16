"""
Photos router — upload and manage photos (teacher endpoints).
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_teacher, get_storage
from ..services.photo_service import PhotoService
from ..utils.s3 import S3Client
from ..models.user import User

router = APIRouter(prefix="/api/v1/photos", tags=["photos"])


@router.post("/upload", status_code=201)
async def upload_photos(
    playgroup_id: Annotated[UUID, Form()],
    files: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """
    Upload one or more photos to a playgroup.

    - Max 20 files per request
    - Max 10MB per file
    - Accepted formats: JPEG, PNG, HEIC, WebP
    - Photos are queued for face processing automatically
    """
    if len(files) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 files per upload")

    # Verify teacher belongs to this playgroup
    if current_user.playgroup_id != playgroup_id:
        raise HTTPException(status_code=403, detail="Not authorized for this playgroup")

    service = PhotoService(db, storage)
    result = await service.upload_batch(
        files=files,
        playgroup_id=playgroup_id,
        uploaded_by=current_user.id,
    )

    return result


@router.get("/my-uploads")
async def get_my_uploads(
    page: int = 1,
    limit: int = 20,
    date: str | None = None,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """Get paginated list of photos uploaded by the current teacher."""
    service = PhotoService(db, storage)
    return await service.get_teacher_uploads(
        teacher_id=current_user.id,
        page=page,
        limit=limit,
        date_filter=date,
    )


@router.delete("/{photo_id}", status_code=204)
async def delete_photo(
    photo_id: UUID,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """Delete a photo (only by its uploader)."""
    service = PhotoService(db, storage)
    deleted = await service.delete_photo(photo_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Photo not found or not authorized")
