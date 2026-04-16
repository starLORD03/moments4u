"""Photo model — uploaded images with metadata and expiry."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, BigInteger, Boolean, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ..database import Base


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_thumbnail_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    original_filename: Mapped[str | None] = mapped_column(String(255), nullable=True)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False, default="image/jpeg")
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        SAEnum("uploading", "processing", "ready", "failed", name="photo_status", create_type=False),
        nullable=False,
        default="uploading",
    )
    playgroup_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("playgroups.id", ondelete="CASCADE"), nullable=False
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    captured_at: Mapped[datetime | None] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    playgroup = relationship("Playgroup", back_populates="photos")
    uploader = relationship("User", back_populates="photos")
    faces = relationship("Face", back_populates="photo", cascade="all, delete-orphan")

    # Indexes
    __table_args__ = (
        Index("idx_photos_expires_at", "expires_at"),
        Index("idx_photos_playgroup_created", "playgroup_id", created_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<Photo {self.id} ({self.status})>"
