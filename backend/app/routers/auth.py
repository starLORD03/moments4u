"""
Auth router — register, login, refresh, logout.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, Cookie
from sqlalchemy.ext.asyncio import AsyncSession

from ..dependencies import get_db, get_current_user
from ..services.auth_service import AuthService
from ..schemas.auth import (
    RegisterRequest,
    LoginRequest,
    AuthResponse,
    TokenRefreshResponse,
    UserResponse,
)
from ..utils.security import decode_refresh_token, create_access_token
from ..models.user import User

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Register a new user account."""
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.register(
            email=body.email,
            password=body.password,
            full_name=body.full_name,
            role=body.role,
            playgroup_id=body.playgroup_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    # Set refresh token as HTTP-only cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,  # 7 days
        path="/api/v1/auth",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Authenticate with email and password."""
    service = AuthService(db)
    try:
        user, access_token, refresh_token = await service.login(
            email=body.email,
            password=body.password,
        )
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
        path="/api/v1/auth",
    )

    return AuthResponse(
        user=UserResponse.model_validate(user),
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_token: str | None = Cookie(None),
):
    """Get a new access token using the refresh token cookie."""
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    payload = decode_refresh_token(refresh_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = payload.get("sub")
    service = AuthService(db)
    user = await service.get_user_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found")

    new_access_token = create_access_token(user.id, user.role)
    return TokenRefreshResponse(access_token=new_access_token)


@router.post("/logout", status_code=204)
async def logout(response: Response):
    """Clear the refresh token cookie."""
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/auth",
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get the current authenticated user."""
    return UserResponse.model_validate(current_user)
