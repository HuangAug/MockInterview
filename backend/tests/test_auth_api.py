"""Tests for Auth API routes (T012)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.exceptions import AppException
from app.db.session import get_db
from app.main import app
from app.models.user import User

FIXED_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


def _mock_user() -> User:
    return User(
        id=FIXED_UUID,
        email="test@example.com",
        password_hash="hashed",
        display_name="TestUser",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture(autouse=True)
def reset_overrides() -> None:
    """Ensure dependency overrides are cleaned up after each test."""
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()


class TestRegisterEndpoint:
    """POST /api/v1/auth/register"""

    @pytest.mark.asyncio
    async def test_register_success_returns_201(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_user = _mock_user()
        with patch(
            "app.services.auth_service.AuthService.register",
            new_callable=AsyncMock,
            return_value=(mock_user, "access_jwt", "a" * 128),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "test@example.com",
                        "password": "Pass1234",
                        "displayName": "TestUser",
                    },
                )

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "注册成功"
        assert body["data"]["user"]["email"] == "test@example.com"
        assert body["data"]["tokens"]["tokenType"] == "Bearer"
        assert body["data"]["tokens"]["expiresIn"] == 900

    @pytest.mark.asyncio
    async def test_register_weak_password_returns_400(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.services.auth_service.AuthService.register",
            new_callable=AsyncMock,
            side_effect=AppException(code=40002, message="密码不符合要求", status_code=400),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                # Password passes Pydantic length check but fails business rule
                resp = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "a@b.com",
                        "password": "nonletters",
                        "displayName": "X",
                    },
                )

        assert resp.status_code == 400
        body = resp.json()
        assert body["success"] is False
        assert body["error"]["code"] == 40002

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.services.auth_service.AuthService.register",
            new_callable=AsyncMock,
            side_effect=AppException(code=40902, message="邮箱已被注册", status_code=409),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "dup@example.com",
                        "password": "Pass1234",
                        "displayName": "Dup",
                    },
                )

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == 40902


class TestLoginEndpoint:
    """POST /api/v1/auth/login"""

    @pytest.mark.asyncio
    async def test_login_success(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_user = _mock_user()
        with patch(
            "app.services.auth_service.AuthService.login",
            new_callable=AsyncMock,
            return_value=(mock_user, "access_jwt", "b" * 128),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "Pass1234"},
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["user"]["email"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_login_invalid_returns_401(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.services.auth_service.AuthService.login",
            new_callable=AsyncMock,
            side_effect=AppException(code=40102, message="邮箱或密码错误", status_code=401),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "wrong@example.com", "password": "WrongPass1"},
                )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == 40102


class TestRefreshEndpoint:
    """POST /api/v1/auth/refresh"""

    @pytest.mark.asyncio
    async def test_refresh_success(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.services.auth_service.AuthService.refresh",
            new_callable=AsyncMock,
            return_value=("new_access", "c" * 128),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refreshToken": "d" * 128},
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["accessToken"] == "new_access"

    @pytest.mark.asyncio
    async def test_refresh_invalid_returns_401(self) -> None:
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        with patch(
            "app.services.auth_service.AuthService.refresh",
            new_callable=AsyncMock,
            side_effect=AppException(code=40103, message="Refresh Token 无效", status_code=401),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refreshToken": "invalid"},
                )

        assert resp.status_code == 401
        assert resp.json()["error"]["code"] == 40103


class TestLogoutEndpoint:
    """POST /api/v1/auth/logout"""

    @pytest.mark.asyncio
    async def test_logout_without_token_returns_403(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/auth/logout",
                json={"refreshToken": "x" * 128},
            )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_logout_success(self) -> None:
        mock_db = AsyncMock()
        mock_user = _mock_user()
        app.dependency_overrides[get_db] = lambda: mock_db

        from app.api.deps import get_current_user

        app.dependency_overrides[get_current_user] = lambda: mock_user

        with patch(
            "app.services.auth_service.AuthService.logout",
            new_callable=AsyncMock,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/auth/logout",
                    json={"refreshToken": "e" * 128},
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "已退出登录"


# ===========================================================================
# T038 — Auth flow integration test
# ===========================================================================


class TestAuthFlow:
    """End-to-end auth flow: register → login → refresh → logout (T038)."""

    @pytest.mark.asyncio
    async def test_full_auth_flow(self) -> None:
        """Verify the complete auth lifecycle via HTTP layer."""
        mock_db = AsyncMock()
        app.dependency_overrides[get_db] = lambda: mock_db

        mock_user = _mock_user()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            # Step 1: Register
            with patch(
                "app.services.auth_service.AuthService.register",
                new_callable=AsyncMock,
                return_value=(mock_user, "access_1", "r" * 128),
            ):
                resp = await client.post(
                    "/api/v1/auth/register",
                    json={
                        "email": "test@example.com",
                        "password": "Pass1234",
                        "displayName": "TestUser",
                    },
                )
            assert resp.status_code == 201
            data = resp.json()["data"]
            assert data["tokens"]["accessToken"] == "access_1"

            # Step 2: Login
            with patch(
                "app.services.auth_service.AuthService.login",
                new_callable=AsyncMock,
                return_value=(mock_user, "access_2", "s" * 128),
            ):
                resp = await client.post(
                    "/api/v1/auth/login",
                    json={"email": "test@example.com", "password": "Pass1234"},
                )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["tokens"]["accessToken"] == "access_2"
            refresh_token_2 = data["tokens"]["refreshToken"]
            assert refresh_token_2 == "s" * 128

            # Step 3: Refresh
            with patch(
                "app.services.auth_service.AuthService.refresh",
                new_callable=AsyncMock,
                return_value=("access_3", "t" * 128),
            ):
                resp = await client.post(
                    "/api/v1/auth/refresh",
                    json={"refreshToken": refresh_token_2},
                )
            assert resp.status_code == 200
            data = resp.json()["data"]
            assert data["accessToken"] == "access_3"
            refresh_token_3 = data["refreshToken"]
            assert refresh_token_3 == "t" * 128

            # Step 4: Logout (requires auth header)
            from app.api.deps import get_current_user

            app.dependency_overrides[get_current_user] = lambda: mock_user

            with patch(
                "app.services.auth_service.AuthService.logout",
                new_callable=AsyncMock,
            ):
                resp = await client.post(
                    "/api/v1/auth/logout",
                    json={"refreshToken": refresh_token_3},
                    headers={"Authorization": "Bearer access_3"},
                )
            assert resp.status_code == 200
            body = resp.json()
            assert body["success"] is True
            assert body["message"] == "已退出登录"
