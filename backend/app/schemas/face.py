"""Pydantic schemas for face recognition endpoints."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class FaceItem(BaseModel):
    id: UUID
    photo_id: UUID
    crop_url: str | None = None
    confidence: float
    match_status: str
    child_id: UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RegisterChildFaceResponse(BaseModel):
    child_id: UUID
    reference_face_id: UUID
    crop_url: str | None = None
    matched_photos_count: int


class FaceAssignRequest(BaseModel):
    child_id: UUID


class FaceAssignResponse(BaseModel):
    face_id: UUID
    child_id: UUID
    match_status: str


class UnmatchedFacesResponse(BaseModel):
    faces: list[FaceItem]
