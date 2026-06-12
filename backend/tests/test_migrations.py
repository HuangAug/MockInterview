"""Tests for database migration files 001-003."""

import importlib.util
from pathlib import Path

import pytest

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"


def _load_migration(filename: str):
    """Dynamically load a migration module."""
    path = MIGRATIONS_DIR / filename
    spec = importlib.util.spec_from_file_location(filename, path)
    assert spec is not None, f"Cannot find spec for {filename}"
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigrationFilesExist:
    """All three migration files must exist."""

    @pytest.mark.parametrize(
        "filename",
        [
            "001_create_job_roles.py",
            "002_create_users.py",
            "003_create_refresh_tokens.py",
        ],
    )
    def test_migration_file_exists(self, filename: str) -> None:
        assert (MIGRATIONS_DIR / filename).is_file()


class TestMigration001JobRoles:
    """Verify job_roles migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("001_create_job_roles.py")
        assert mod.revision == "001"

    def test_no_down_revision(self) -> None:
        mod = _load_migration("001_create_job_roles.py")
        assert mod.down_revision is None

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("001_create_job_roles.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("001_create_job_roles.py")
        assert callable(mod.downgrade)


class TestMigration002Users:
    """Verify users migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("002_create_users.py")
        assert mod.revision == "002"

    def test_down_revision_is_001(self) -> None:
        mod = _load_migration("002_create_users.py")
        assert mod.down_revision == "001"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("002_create_users.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("002_create_users.py")
        assert callable(mod.downgrade)


class TestMigration003RefreshTokens:
    """Verify refresh_tokens migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("003_create_refresh_tokens.py")
        assert mod.revision == "003"

    def test_down_revision_is_002(self) -> None:
        mod = _load_migration("003_create_refresh_tokens.py")
        assert mod.down_revision == "002"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("003_create_refresh_tokens.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("003_create_refresh_tokens.py")
        assert callable(mod.downgrade)


class TestMigrationRevisionChain:
    """Verify the complete revision chain: None → 001 → 002 → 003."""

    def test_revision_chain_is_continuous(self) -> None:
        m001 = _load_migration("001_create_job_roles.py")
        m002 = _load_migration("002_create_users.py")
        m003 = _load_migration("003_create_refresh_tokens.py")

        assert m001.down_revision is None
        assert m002.down_revision == m001.revision
        assert m003.down_revision == m002.revision
