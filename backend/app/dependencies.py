"""
FastAPI dependency injection — database sessions, current user, storage client.

These are injected into route handlers via Depends().
"""

from typing import Annotated, AsyncGenerator
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .database import async_session_factory, SyncSessionFactory
from .models.user import User
from .utils.security import decode_access_token
from .utils.s3 import S3Client
from .config import get_settings

security_scheme = HTTPBearer()


# ── Database session ──

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, auto-close on exit."""
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_db():
    """Return a sync database session (for Celery workers)."""
    session = SyncSessionFactory()
    try:
        return session
    except Exception:
        session.close()
        raise


# ── Current user ──

async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """Decode JWT and return the authenticated user."""
    token = credentials.credentials
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


async def get_current_teacher(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require current user to have the 'teacher' role."""
    if current_user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher access required")
    return current_user


async def get_current_parent(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require current user to have the 'parent' role."""
    if current_user.role not in ("parent", "admin"):
        raise HTTPException(status_code=403, detail="Parent access required")
    return current_user


async def get_current_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Require current user to have the 'admin' role."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── S3 Storage ──

def get_storage() -> S3Client:
    """Return an S3 client instance."""
    settings = get_settings()
    return S3Client(
        endpoint_url=settings.s3_endpoint_url,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
        bucket_name=settings.s3_bucket_name,
        region=settings.s3_region,
    )
