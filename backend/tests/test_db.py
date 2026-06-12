"""Tests for database and Alembic configuration."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base
from app.db.session import async_session_factory, engine


def test_base_metadata_exists() -> None:
    """Base class has a metadata attribute for Alembic autogenerate."""
    assert Base.metadata is not None


def test_engine_url_configured() -> None:
    """Engine URL is loaded from Settings (not empty)."""
    url = str(engine.url)
    assert url != ""
    assert "postgresql" in url or "asyncpg" in url or "sqlite" in url


def test_session_factory_returns_async_session() -> None:
    """Session factory produces AsyncSession instances."""
    session = async_session_factory()
    assert isinstance(session, AsyncSession)
