"""
Database engine and session management.

Provides both async (for FastAPI) and sync (for Celery) session factories.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from sqlalchemy import create_engine as create_sync_engine

from .config import get_settings

settings = get_settings()

# ── Async engine (FastAPI) ──
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug and not settings.is_production,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# ── Sync engine (Celery workers) ──
sync_engine = create_sync_engine(
    settings.database_url_sync,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
)

SyncSessionFactory = sessionmaker(bind=sync_engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass
