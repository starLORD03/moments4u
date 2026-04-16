"""Face and ChildReferenceFace models — face detections and reference embeddings."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as PGUUID
from pgvector.sqlalchemy import Vector
from sqlalchemy.ext.compiler import compiles

from ..database import Base

@compiles(Vector, "sqlite")
def compile_vector_sqlite(element, compiler, **kw):
    return "TEXT"


class Face(Base):
    """A detected face within an uploaded photo."""

    __tablename__ = "faces"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    photo_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("photos.id", ondelete="CASCADE"), nullable=False
    )
    child_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("children.id", ondelete="SET NULL"), nullable=True
    )
    bbox_x: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_y: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_w: Mapped[int] = mapped_column(Integer, nullable=False)
    bbox_h: Mapped[int] = mapped_column(Integer, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    embedding = mapped_column(Vector(512), nullable=False)
    s3_crop_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    match_status: Mapped[str] = mapped_column(
        SAEnum("matched", "unmatched", "ignored", name="face_match_status", create_type=False),
        nullable=False,
        default="unmatched",
    )
    match_distance: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    photo = relationship("Photo", back_populates="faces")
    child = relationship("Child", back_populates="faces")

    __table_args__ = (
        Index("idx_faces_child", "child_id"),
    )

    @staticmethod
    def generate_id() -> str:
        return str(uuid.uuid4())

    def __repr__(self) -> str:
        return f"<Face {self.id} match={self.match_status}>"


class ChildReferenceFace(Base):
    """Reference face embedding for a child — used for matching."""

    __tablename__ = "child_reference_faces"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    child_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), nullable=False
    )
    embedding = mapped_column(Vector(512), nullable=False)
    s3_crop_key: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    child = relationship("Child", back_populates="reference_faces")

    def __repr__(self) -> str:
        return f"<ChildReferenceFace child={self.child_id}>"
