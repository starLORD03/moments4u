"""
Authentication service — registration, login, and token management.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from ..utils.security import hash_password, verify_password, create_access_token, create_refresh_token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def register(
        self,
        email: str,
        password: str,
        full_name: str,
        role: str,
        playgroup_id: UUID | None = None,
    ) -> tuple[User, str, str]:
        """
        Register a new user.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ValueError: If email already exists.
        """
        # Check for existing email
        existing = await self.db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role=role,
            playgroup_id=playgroup_id,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Authenticate a user by email + password.

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            ValueError: If credentials are invalid.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.password_hash):
            raise ValueError("Invalid email or password")

        if not user.is_active:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(user.id, user.role)
        refresh_token = create_refresh_token(user.id)

        return user, access_token, refresh_token

    async def get_user_by_id(self, user_id: UUID) -> User | None:
        """Fetch a user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()
