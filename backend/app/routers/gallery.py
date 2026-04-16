"""
Gallery router — parent-facing endpoints for viewing child's photos.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_parent, get_storage
from ..services.face_service import FaceService
from ..utils.s3 import S3Client
from ..models.user import User

router = APIRouter(prefix="/api/v1/gallery", tags=["gallery"])


@router.get("/children/{child_id}")
async def get_child_gallery(
    child_id: UUID,
    page: int = 1,
    limit: int = 20,
    date_from: str | None = None,
    date_to: str | None = None,
    current_user: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
    storage: S3Client = Depends(get_storage),
):
    """
    Get a timeline gallery of photos containing the specified child.

    Requires parent role and verified parent-child relationship.
    Photos are grouped by day and returned with signed URLs.
    """
    service = FaceService(db, storage)
    try:
        return await service.get_child_gallery(
            child_id=child_id,
            parent_id=current_user.id,
            page=page,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/my-children")
async def get_my_children(
    current_user: User = Depends(get_current_parent),
    db: AsyncSession = Depends(get_db),
):
    """Get the list of children linked to the current parent."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from ..models.user import User as UserModel

    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.children))
        .where(UserModel.id == current_user.id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "children": [
            {
                "id": child.id,
                "full_name": child.full_name,
                "date_of_birth": child.date_of_birth,
            }
            for child in user.children
        ]
    }
