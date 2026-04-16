"""Pydantic schemas for photo upload and gallery responses."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class PhotoItem(BaseModel):
    id: UUID
    thumbnail_url: str | None = None
    status: str
    face_count: int = 0
    captured_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoUploadResult(BaseModel):
    id: UUID
    thumbnail_url: str | None = None
    status: str
    created_at: datetime


class PhotoUploadFailure(BaseModel):
    filename: str
    error: str


class PhotoUploadResponse(BaseModel):
    uploaded: list[PhotoUploadResult]
    failed: list[PhotoUploadFailure]


class PhotoDetail(BaseModel):
    id: UUID
    image_url: str
    thumbnail_url: str | None = None
    captured_at: datetime | None = None
    playgroup_name: str | None = None
    faces: list["FaceInPhoto"] = []


class FaceInPhoto(BaseModel):
    face_crop_url: str | None = None
    is_my_child: bool = False
    confidence: float


class PaginationMeta(BaseModel):
    page: int
    limit: int
    total: int
    total_pages: int


class PhotoListResponse(BaseModel):
    photos: list[PhotoItem]
    pagination: PaginationMeta


class TimelineDay(BaseModel):
    date: str  # YYYY-MM-DD
    photos: list[PhotoItem]


class GalleryResponse(BaseModel):
    child: "ChildBrief"
    timeline: list[TimelineDay]
    pagination: PaginationMeta


class ChildBrief(BaseModel):
    id: UUID
    full_name: str

    model_config = {"from_attributes": True}
