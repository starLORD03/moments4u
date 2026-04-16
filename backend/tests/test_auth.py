"""Tests for authentication endpoints."""

import pytest


@pytest.mark.asyncio
async def test_health_check(client):
    """Health endpoint should return 200."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "moments4u"


@pytest.mark.asyncio
async def test_register_success(client):
    """Registration with valid data should return 201."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "securepassword123",
            "full_name": "Test User",
            "role": "parent",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["user"]["email"] == "test@example.com"
    assert data["user"]["role"] == "parent"
    assert "access_token" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client):
    """Duplicate email registration should return 409."""
    payload = {
        "email": "dupe@example.com",
        "password": "securepassword123",
        "full_name": "User One",
        "role": "teacher",
    }
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client):
    """Login with correct credentials should return tokens."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "password": "mypassword123",
            "full_name": "Login User",
            "role": "teacher",
        },
    )

    # Login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "mypassword123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    """Login with wrong password should return 401."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "correctpassword",
            "full_name": "Wrong Pass",
            "role": "parent",
        },
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "incorrectpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_unauthorized(client):
    """Accessing /me without token should return 403."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 403
