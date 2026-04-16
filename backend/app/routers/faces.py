"""
Faces router — face registration, unmatched face listing, manual assignment.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_parent, get_current_teacher, get_storage
from ..services.face_service import FaceService
from ..schemas.face import FaceAssignRequest
from ..utils.s3 import S3Client
from ..utils.face_engine import FaceEngine
from ..models.user import User

router = APIRouter(prefix="/api/v1/faces", tags=["faces"])


@router.post("/register-child", status_code=201)
async def register_child_face(
    child_id: Annotated[UUID, Form()],
    photo: UploadFile = File(...),
    current_user: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """
    Register a child's face for automatic matching.

    Upload a clear photo of the child's face. The system will:
    1. Detect the face and generate an embedding
    2. Save it as a reference
    3. Retroactively match all unmatched faces in the playgroup
    """
    service = FaceService(db, storage)

    # Verify parent-child relationship
    if not await service.verify_parent_child(current_user.id, child_id):
        raise HTTPException(status_code=403, detail="Not parent of this child")

    # Read and process the uploaded photo
    content = await photo.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    # Detect face and get embedding
    engine = FaceEngine()
    embedding = engine.get_single_embedding(content, min_confidence=0.7)

    if embedding is None:
        raise HTTPException(
            status_code=422,
            detail="No clear face detected. Please upload a well-lit, front-facing photo.",
        )

    # Save face crop to S3
    import io
    from PIL import Image

    faces = engine.detect_and_embed(content, min_confidence=0.7)
    crop_key = None
    if faces:
        crop_buffer = io.BytesIO()
        faces[0]["crop"].save(crop_buffer, format="JPEG", quality=90)
        crop_key = f"references/{child_id}/{UUID(int=0).hex[:8]}.jpg"
        await storage.upload(
            key=crop_key,
            data=crop_buffer.getvalue(),
            content_type="image/jpeg",
        )

    result = await service.register_reference_face(
        child_id=child_id,
        embedding=embedding.tolist(),
        crop_key=crop_key,
    )

    return result


@router.get("/unmatched")
async def get_unmatched_faces(
    playgroup_id: UUID,
    page: int = 1,
    limit: int = 50,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """Get unmatched faces in a playgroup for manual review."""
    service = FaceService(db, storage)
    faces = await service.get_unmatched_faces(
        playgroup_id=playgroup_id,
        page=page,
        limit=limit,
    )
    return {"faces": faces}


@router.post("/{face_id}/assign")
async def assign_face(
    face_id: UUID,
    body: FaceAssignRequest,
    current_user: User = Depends(get_current_teacher),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """Manually assign a face to a child."""
    service = FaceService(db, storage)
    try:
        return await service.assign_face_to_child(face_id, body.child_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
