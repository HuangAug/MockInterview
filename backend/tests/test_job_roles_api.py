"""Tests for Job Roles API (T014)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.db.session import get_db
from app.main import app
from app.models.job_role import JobRole
from app.models.user import User

FIXED_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")
USER_UUID = uuid.UUID("b1000001-0000-4000-8000-000000000001")


def _mock_user() -> User:
    return User(
        id=USER_UUID,
        email="test@example.com",
        password_hash="hashed",
        display_name="TestUser",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _mock_job_role(
    sort_order: int, code: str, name_zh: str, name_en: str
) -> JobRole:
    return JobRole(
        id=uuid.UUID(f"a1000001-0000-4000-8000-00000000000{sort_order}"),
        code=code,
        name_zh=name_zh,
        name_en=name_en,
        description=f"Description for {name_en}",
        sort_order=sort_order,
        is_active=True,
    )


def _mock_roles_result(roles: list[JobRole]) -> MagicMock:
    """Build a mock SQLAlchemy result with scalars().all()."""
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = roles
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    return mock_result


@pytest.fixture(autouse=True)
def reset_overrides() -> None:
    """Ensure dependency overrides are cleaned up after each test."""
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()


class TestListJobRoles:
    """GET /api/v1/job-roles"""

    @pytest.mark.asyncio
    async def test_returns_8_roles_sorted_by_sort_order(self) -> None:
        roles = [
            _mock_job_role(1, "frontend", "前端工程师", "Frontend Engineer"),
            _mock_job_role(2, "backend", "后端工程师", "Backend Engineer"),
            _mock_job_role(3, "fullstack", "全栈工程师", "Full Stack Engineer"),
            _mock_job_role(4, "mobile", "移动端工程师", "Mobile Engineer"),
            _mock_job_role(5, "product", "产品经理", "Product Manager"),
            _mock_job_role(6, "data_analyst", "数据分析师", "Data Analyst"),
            _mock_job_role(7, "algorithm", "算法工程师", "Algorithm Engineer"),
            _mock_job_role(8, "test_engineer", "测试工程师", "Test Engineer"),
        ]

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_mock_roles_result(roles))

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/job-roles")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True

        items = body["data"]["items"]
        assert len(items) == 8

        # Verify sort order
        for i, item in enumerate(items, start=1):
            assert item["sortOrder"] == i

        # Verify camelCase field names
        first = items[0]
        assert "nameZh" in first
        assert "nameEn" in first
        assert "sortOrder" in first
        assert first["code"] == "frontend"
        assert first["nameZh"] == "前端工程师"

    @pytest.mark.asyncio
    async def test_returns_only_active_roles(self) -> None:
        """Inactive roles should not appear in the response."""
        active_role = _mock_job_role(1, "frontend", "前端工程师", "Frontend Engineer")

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_mock_roles_result([active_role]))

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/job-roles")

        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert len(items) == 1
        assert items[0]["code"] == "frontend"

    @pytest.mark.asyncio
    async def test_requires_authentication(self) -> None:
        """Unauthenticated requests should be rejected (403 from HTTPBearer)."""
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/job-roles")

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_empty_list_when_no_active_roles(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_mock_roles_result([]))

        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: _mock_user()

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/job-roles")

        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        assert items == []
