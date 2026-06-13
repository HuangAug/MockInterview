"""AuthService — register, login, refresh, logout business logic."""

import re
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User

_PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d).{8,64}$")


class AuthService:
    """Handles authentication business logic: register, login, refresh, logout."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def register(
        self, email: str, password: str, display_name: str
    ) -> tuple[User, str, str]:
        """Register a new user and return (user, access_token, refresh_token).

        Raises:
            AppException(40002): Weak password.
            AppException(40902): Email already registered.
        """
        if not _PASSWORD_RE.match(password):
            raise AppException(
                code=40002, message="密码不符合要求", status_code=400
            )

        existing = await self._db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        if existing.scalar_one_or_none() is not None:
            raise AppException(
                code=40902, message="邮箱已被注册", status_code=409
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            display_name=display_name,
        )
        self._db.add(user)
        await self._db.flush()

        access_token, refresh_token = await self._issue_tokens(user.id)
        return user, access_token, refresh_token

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """Authenticate and return (user, access_token, refresh_token).

        Raises:
            AppException(40102): Invalid credentials.
        """
        result = await self._db.execute(
            select(User).where(User.email == email, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise AppException(
                code=40102, message="邮箱或密码错误", status_code=401
            )

        access_token, refresh_token = await self._issue_tokens(user.id)
        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """Rotate refresh token and return (new_access_token, new_refresh_token).

        Raises:
            AppException(40103): Invalid/expired/revoked refresh token.
        """
        token_hash = hash_refresh_token(refresh_token)
        result = await self._db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        rt = result.scalar_one_or_none()

        now = datetime.now(UTC)
        if rt is None or rt.expires_at < now:
            raise AppException(
                code=40103,
                message="Refresh Token 无效或已过期",
                status_code=401,
            )

        # Revoke old token
        await self._db.execute(
            update(RefreshToken)
            .where(RefreshToken.id == rt.id)
            .values(revoked_at=now)
        )

        # Issue new pair
        new_access, new_refresh = await self._issue_tokens(rt.user_id)
        return new_access, new_refresh

    async def logout(self, refresh_token: str) -> None:
        """Revoke the given refresh token."""
        token_hash = hash_refresh_token(refresh_token)
        now = datetime.now(UTC)
        await self._db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )

    async def _issue_tokens(self, user_id: UUID) -> tuple[str, str]:
        """Create and persist a new access + refresh token pair."""
        access_token = create_access_token(user_id)
        refresh_token = create_refresh_token()

        expires_at = datetime.now(UTC) + timedelta(
            days=settings.refresh_token_expire_days
        )
        rt = RefreshToken(
            user_id=user_id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=expires_at,
        )
        self._db.add(rt)
        await self._db.flush()

        return access_token, refresh_token
