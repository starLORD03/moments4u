"""Pydantic schemas for child management."""

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field


class ChildCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    date_of_birth: date | None = None
    playgroup_id: UUID


class ChildResponse(BaseModel):
    id: UUID
    full_name: str
    date_of_birth: date | None = None
    playgroup_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ChildListResponse(BaseModel):
    children: list[ChildResponse]
