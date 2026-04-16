"""Child model — represents a child enrolled in a playgroup."""

import uuid
from datetime import date, datetime, timezone

from sqlalchemy import String, Date, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID

from ..database import Base

# Many-to-many: parents ↔ children
parent_children = Table(
    "parent_children",
    Base.metadata,
    Column("parent_id", PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("child_id", PGUUID(as_uuid=True), ForeignKey("children.id", ondelete="CASCADE"), primary_key=True),
)


class Child(Base):
    __tablename__ = "children"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    playgroup_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("playgroups.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    playgroup = relationship("Playgroup", back_populates="children")
    parents = relationship("User", secondary=parent_children, back_populates="children")
    faces = relationship("Face", back_populates="child")
    reference_faces = relationship("ChildReferenceFace", back_populates="child")

    def __repr__(self) -> str:
        return f"<Child {self.full_name}>"
