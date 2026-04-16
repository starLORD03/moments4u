"""
Admin router — playgroup and child management.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_user, get_current_admin
from ..models.user import User
from ..models.playgroup import Playgroup
from ..models.child import Child
from ..schemas.child import ChildCreate, ChildResponse

router = APIRouter(prefix="/api/v1", tags=["admin"])


# ── Playgroups ──

@router.get("/playgroups/{playgroup_id}")
async def get_playgroup(
    playgroup_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get playgroup details."""
    result = await db.execute(select(Playgroup).where(Playgroup.id == playgroup_id))
    pg = result.scalar_one_or_none()
    if not pg:
        raise HTTPException(status_code=404, detail="Playgroup not found")

    return {
        "id": pg.id,
        "name": pg.name,
        "description": pg.description,
        "is_active": pg.is_active,
        "created_at": pg.created_at,
    }


@router.get("/playgroups/{playgroup_id}/children")
async def list_children(
    playgroup_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all children in a playgroup."""
    result = await db.execute(
        select(Child)
        .where(Child.playgroup_id == playgroup_id)
        .order_by(Child.full_name)
    )
    children = result.scalars().all()

    return {
        "children": [
            ChildResponse.model_validate(c) for c in children
        ]
    }


@router.post("/playgroups/{playgroup_id}/children", status_code=201)
async def add_child(
    playgroup_id: UUID,
    body: ChildCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Add a child to a playgroup (admin only)."""
    child = Child(
        full_name=body.full_name,
        date_of_birth=body.date_of_birth,
        playgroup_id=playgroup_id,
    )
    db.add(child)
    await db.commit()
    await db.refresh(child)
    return ChildResponse.model_validate(child)


@router.get("/playgroups/{playgroup_id}/members")
async def list_members(
    playgroup_id: UUID,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all members of a playgroup (admin only)."""
    result = await db.execute(
        select(User)
        .where(User.playgroup_id == playgroup_id)
        .order_by(User.role, User.full_name)
    )
    users = result.scalars().all()

    return {
        "members": [
            {
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
            }
            for u in users
        ]
    }
