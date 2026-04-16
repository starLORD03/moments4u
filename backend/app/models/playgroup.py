"""Playgroup model — represents a childcare group."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import String, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Uuid as PGUUID

from ..database import Base


class Playgroup(Base):
    __tablename__ = "playgroups"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    members = relationship("User", back_populates="playgroup")
    children = relationship("Child", back_populates="playgroup")
    photos = relationship("Photo", back_populates="playgroup")

    def __repr__(self) -> str:
        return f"<Playgroup {self.name}>"
