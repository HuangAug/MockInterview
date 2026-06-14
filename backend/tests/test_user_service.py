"""Tests for UserService (T015)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import AppException
from app.models.job_role import JobRole
from app.models.user import User
from app.services.user_service import UserService

USER_UUID = uuid.UUID("b1000001-0000-4000-8000-000000000001")
JOB_ROLE_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


def _mock_user(**kwargs: object) -> User:
    defaults = {
        "id": USER_UUID,
        "email": "test@example.com",
        "password_hash": "hashed",
        "display_name": "TestUser",
        "target_job_role_id": None,
        "avatar_url": None,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }
    defaults.update(kwargs)
    return User(**defaults)  # type: ignore[arg-type]


def _mock_job_role() -> JobRole:
    return JobRole(
        id=JOB_ROLE_UUID,
        code="frontend",
        name_zh="前端工程师",
        name_en="Frontend Engineer",
        description="Frontend dev",
        sort_order=1,
        is_active=True,
    )


def _make_result(scalar: object | None) -> MagicMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = scalar
    return mock_result


class TestGetMe:
    """UserService.get_me"""

    @pytest.mark.asyncio
    async def test_returns_user_with_no_job_role(self) -> None:
        mock_db = AsyncMock()
        user = _mock_user()
        mock_db.execute = AsyncMock(return_value=_make_result(user))

        svc = UserService(mock_db)
        result_user, role_name = await svc.get_me(USER_UUID)

        assert result_user == user
        assert role_name is None

    @pytest.mark.asyncio
    async def test_returns_user_with_job_role_name(self) -> None:
        mock_db = AsyncMock()
        user = _mock_user(target_job_role_id=JOB_ROLE_UUID)

        # First call: find user, second call: find job role
        mock_db.execute = AsyncMock(
            side_effect=[_make_result(user), _make_result(_mock_job_role())]
        )

        svc = UserService(mock_db)
        result_user, role_name = await svc.get_me(USER_UUID)

        assert result_user == user
        assert role_name == "前端工程师"

    @pytest.mark.asyncio
    async def test_raises_40401_when_user_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = UserService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.get_me(USER_UUID)

        assert exc_info.value.code == 40401


class TestUpdateMe:
    """UserService.update_me"""

    @pytest.mark.asyncio
    async def test_update_display_name(self) -> None:
        mock_db = AsyncMock()
        user = _mock_user()
        mock_db.execute = AsyncMock(return_value=_make_result(user))
        mock_db.flush = AsyncMock()

        svc = UserService(mock_db)
        result_user, role_name = await svc.update_me(USER_UUID, display_name="NewName")

        assert result_user.display_name == "NewName"
        assert role_name is None

    @pytest.mark.asyncio
    async def test_update_target_job_role_valid(self) -> None:
        mock_db = AsyncMock()
        user = _mock_user()
        jr = _mock_job_role()

        # Call 1: find user, Call 2: validate job role, Call 3: resolve name
        mock_db.execute = AsyncMock(
            side_effect=[_make_result(user), _make_result(jr), _make_result(jr)]
        )
        mock_db.flush = AsyncMock()

        svc = UserService(mock_db)
        result_user, role_name = await svc.update_me(
            USER_UUID, target_job_role_id=JOB_ROLE_UUID, update_target_job_role=True
        )

        assert result_user.target_job_role_id == JOB_ROLE_UUID
        assert role_name == "前端工程师"

    @pytest.mark.asyncio
    async def test_update_invalid_job_role_raises_40402(self) -> None:
        mock_db = AsyncMock()
        user = _mock_user()

        # Call 1: find user, Call 2: validate job role (not found)
        mock_db.execute = AsyncMock(
            side_effect=[_make_result(user), _make_result(None)]
        )
        mock_db.flush = AsyncMock()

        svc = UserService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.update_me(
                USER_UUID, target_job_role_id=uuid.uuid4(), update_target_job_role=True
            )

        assert exc_info.value.code == 40402

    @pytest.mark.asyncio
    async def test_update_user_not_found_raises_40401(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = UserService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.update_me(USER_UUID, display_name="X")

        assert exc_info.value.code == 40401
