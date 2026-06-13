"""Tests for Users API (T015)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.main import app
from app.models.user import User

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


@pytest.fixture(autouse=True)
def reset_overrides() -> None:
    """Ensure dependency overrides are cleaned up after each test."""
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()


class TestGetMe:
    """GET /api/v1/users/me"""

    @pytest.mark.asyncio
    async def test_get_me_success(self) -> None:
        mock_db = AsyncMock()
        mock_user = _mock_user()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with patch(
            "app.services.user_service.UserService.get_me",
            new_callable=AsyncMock,
            return_value=(mock_user, None),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/users/me")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["email"] == "test@example.com"
        assert body["data"]["displayName"] == "TestUser"

    @pytest.mark.asyncio
    async def test_get_me_with_job_role(self) -> None:
        mock_db = AsyncMock()
        mock_user = _mock_user(target_job_role_id=JOB_ROLE_UUID)
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: mock_user

        with patch(
            "app.services.user_service.UserService.get_me",
            new_callable=AsyncMock,
            return_value=(mock_user, "前端工程师"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/users/me")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["targetJobRoleId"] == str(JOB_ROLE_UUID)
        assert data["targetJobRoleName"] == "前端工程师"

    @pytest.mark.asyncio
    async def test_get_me_requires_auth(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/users/me")

        assert resp.status_code == 403


class TestUpdateMe:
    """PATCH /api/v1/users/me"""

    @pytest.mark.asyncio
    async def test_update_display_name(self) -> None:
        mock_db = AsyncMock()
        mock_user = _mock_user(display_name="NewName")
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        with patch(
            "app.services.user_service.UserService.update_me",
            new_callable=AsyncMock,
            return_value=(mock_user, None),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.patch(
                    "/api/v1/users/me",
                    json={"displayName": "NewName"},
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["displayName"] == "NewName"
        assert body["message"] == "更新成功"

    @pytest.mark.asyncio
    async def test_update_target_job_role_id(self) -> None:
        mock_db = AsyncMock()
        mock_user = _mock_user(target_job_role_id=JOB_ROLE_UUID)
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        with patch(
            "app.services.user_service.UserService.update_me",
            new_callable=AsyncMock,
            return_value=(mock_user, "前端工程师"),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.patch(
                    "/api/v1/users/me",
                    json={"targetJobRoleId": str(JOB_ROLE_UUID)},
                )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["targetJobRoleId"] == str(JOB_ROLE_UUID)
        assert data["targetJobRoleName"] == "前端工程师"

    @pytest.mark.asyncio
    async def test_update_invalid_job_role_returns_40402(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        with patch(
            "app.services.user_service.UserService.update_me",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40402, message="岗位不存在", status_code=404
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.patch(
                    "/api/v1/users/me",
                    json={"targetJobRoleId": str(uuid.uuid4())},
                )

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == 40402

    @pytest.mark.asyncio
    async def test_update_display_name_too_long_returns_422(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/api/v1/users/me",
                json={"displayName": "x" * 51},
            )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_requires_auth(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.patch(
                "/api/v1/users/me",
                json={"displayName": "New"},
            )

        assert resp.status_code == 403
