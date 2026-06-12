"""Tests for AuthService (T011)."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.core.security import hash_password, hash_refresh_token
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.services.auth_service import AuthService

FIXED_EMAIL = "test@example.com"
FIXED_PASSWORD = "Pass1234"
FIXED_DISPLAY = "TestUser"
FIXED_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


def _mock_db() -> AsyncMock:
    """Create a mock AsyncSession for AuthService tests."""
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    return db


def _make_user(
    email: str = FIXED_EMAIL,
    password: str = FIXED_PASSWORD,
    user_id: uuid.UUID = FIXED_UUID,
) -> User:
    """Create a User instance for testing."""
    return User(
        id=user_id,
        email=email,
        password_hash=hash_password(password),
        display_name=FIXED_DISPLAY,
    )


def _make_refresh_token(
    user_id: uuid.UUID = FIXED_UUID,
    token_hash: str = "abc",
    expires_delta: timedelta = timedelta(days=7),
    revoked: bool = False,
) -> RefreshToken:
    """Create a RefreshToken instance for testing."""
    return RefreshToken(
        id=uuid.uuid4(),
        user_id=user_id,
        token_hash=token_hash,
        expires_at=datetime.now(UTC) + expires_delta,
        revoked_at=datetime.now(UTC) if revoked else None,
    )


class TestRegister:
    """AuthService.register tests."""

    @pytest.mark.asyncio
    async def test_register_success(self) -> None:
        db = _mock_db()
        # No existing user
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        user, access, refresh = await svc.register(
            FIXED_EMAIL, FIXED_PASSWORD, FIXED_DISPLAY
        )

        assert user.email == FIXED_EMAIL
        assert len(access) > 20
        assert len(refresh) == 128
        db.add.assert_called()

    @pytest.mark.asyncio
    async def test_register_weak_password_raises_40002(self) -> None:
        db = _mock_db()
        svc = AuthService(db)

        with pytest.raises(AppException) as exc_info:
            await svc.register(FIXED_EMAIL, "short", FIXED_DISPLAY)
        assert exc_info.value.code == 40002

    @pytest.mark.asyncio
    async def test_register_no_digit_raises_40002(self) -> None:
        db = _mock_db()
        svc = AuthService(db)

        with pytest.raises(AppException) as exc_info:
            await svc.register(FIXED_EMAIL, "NoDigitHere", FIXED_DISPLAY)
        assert exc_info.value.code == 40002

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_40902(self) -> None:
        db = _mock_db()
        existing_user = _make_user()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_user
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.register(FIXED_EMAIL, FIXED_PASSWORD, FIXED_DISPLAY)
        assert exc_info.value.code == 40902


class TestLogin:
    """AuthService.login tests."""

    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        db = _mock_db()
        user = _make_user()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        u, access, refresh = await svc.login(FIXED_EMAIL, FIXED_PASSWORD)

        assert u.id == FIXED_UUID
        assert len(access) > 20
        assert len(refresh) == 128

    @pytest.mark.asyncio
    async def test_login_wrong_email_raises_40102(self) -> None:
        db = _mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.login("unknown@example.com", FIXED_PASSWORD)
        assert exc_info.value.code == 40102

    @pytest.mark.asyncio
    async def test_login_wrong_password_raises_40102(self) -> None:
        db = _mock_db()
        user = _make_user()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.login(FIXED_EMAIL, "WrongPass1")
        assert exc_info.value.code == 40102


class TestRefresh:
    """AuthService.refresh tests."""

    @pytest.mark.asyncio
    async def test_refresh_success(self) -> None:
        db = _mock_db()
        raw_token = "a" * 128
        token_hash = hash_refresh_token(raw_token)
        rt = _make_refresh_token(token_hash=token_hash)

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = rt
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        new_access, new_refresh = await svc.refresh(raw_token)

        assert len(new_access) > 20
        assert len(new_refresh) == 128

    @pytest.mark.asyncio
    async def test_refresh_invalid_token_raises_40103(self) -> None:
        db = _mock_db()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.refresh("invalid" * 20)
        assert exc_info.value.code == 40103

    @pytest.mark.asyncio
    async def test_refresh_expired_token_raises_40103(self) -> None:
        db = _mock_db()
        raw_token = "b" * 128
        token_hash = hash_refresh_token(raw_token)
        rt = _make_refresh_token(
            token_hash=token_hash, expires_delta=timedelta(days=-1)
        )

        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = rt
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.refresh(raw_token)
        assert exc_info.value.code == 40103

    @pytest.mark.asyncio
    async def test_refresh_revoked_token_raises_40103(self) -> None:
        db = _mock_db()
        raw_token = "c" * 128
        # Revoked tokens are filtered in the WHERE clause, so no mock needed
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        svc = AuthService(db)
        with pytest.raises(AppException) as exc_info:
            await svc.refresh(raw_token)
        assert exc_info.value.code == 40103


class TestLogout:
    """AuthService.logout tests."""

    @pytest.mark.asyncio
    async def test_logout_revokes_token(self) -> None:
        db = _mock_db()
        db.execute = AsyncMock()

        svc = AuthService(db)
        await svc.logout("d" * 128)

        db.execute.assert_called_once()
