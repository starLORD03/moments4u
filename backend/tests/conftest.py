"""
Test fixtures and configuration for pytest.

Provides:
- Test database session
- FastAPI test client
- Sample data factories
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import create_app
from app.database import Base
from app.dependencies import get_db
from app.utils.security import hash_password, create_access_token

# Use true in-memory SQLite for tests to prevent test pollution
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_session():
    """Create a fresh test database for each test."""
    from sqlalchemy.pool import StaticPool
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_session):
    """FastAPI test client with overridden database dependency."""
    app = create_app()

    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def sample_teacher_token():
    """Generate a JWT token for a test teacher."""
    user_id = uuid.uuid4()
    return create_access_token(user_id, "teacher"), user_id


@pytest.fixture
def sample_parent_token():
    """Generate a JWT token for a test parent."""
    user_id = uuid.uuid4()
    return create_access_token(user_id, "parent"), user_id


@pytest.fixture
def auth_headers(sample_teacher_token):
    """Authorization headers for a teacher."""
    token, _ = sample_teacher_token
    return {"Authorization": f"Bearer {token}"}
