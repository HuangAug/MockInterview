"""Tests for seed migration 007 (job_roles seed data)."""

import importlib.util
from pathlib import Path

import pytest

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "alembic" / "versions"

EXPECTED_UUIDS = [
    "a1000001-0000-4000-8000-000000000001",
    "a1000001-0000-4000-8000-000000000002",
    "a1000001-0000-4000-8000-000000000003",
    "a1000001-0000-4000-8000-000000000004",
    "a1000001-0000-4000-8000-000000000005",
    "a1000001-0000-4000-8000-000000000006",
    "a1000001-0000-4000-8000-000000000007",
    "a1000001-0000-4000-8000-000000000008",
]

EXPECTED_CODES = [
    "frontend",
    "backend",
    "fullstack",
    "mobile",
    "product",
    "data_analyst",
    "algorithm",
    "test_engineer",
]


def _load_migration(filename: str):
    """Dynamically load a migration module."""
    path = MIGRATIONS_DIR / filename
    spec = importlib.util.spec_from_file_location(filename, path)
    assert spec is not None, f"Cannot find spec for {filename}"
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestMigration007FileExists:
    """Seed migration file must exist."""

    def test_migration_file_exists(self) -> None:
        assert (MIGRATIONS_DIR / "007_seed_job_roles.py").is_file()


class TestMigration007Structure:
    """Verify revision chain and callable functions."""

    def test_revision_id(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert mod.revision == "007"

    def test_down_revision_is_006(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert mod.down_revision == "006"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert callable(mod.downgrade)


class TestMigration007SeedData:
    """Verify seed data matches DATABASE.md §7.1 and PRD §F-06."""

    def test_has_8_seed_rows(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert len(mod.SEED_ROWS) == 8

    def test_all_expected_uuids_present(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        actual_uuids = [row[0] for row in mod.SEED_ROWS]
        assert actual_uuids == EXPECTED_UUIDS

    def test_all_expected_codes_present(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        actual_codes = [row[1] for row in mod.SEED_ROWS]
        assert actual_codes == EXPECTED_CODES

    @pytest.mark.parametrize(
        "index,expected_zh",
        [
            (0, "前端工程师"),
            (1, "后端工程师"),
            (2, "全栈工程师"),
            (3, "移动端工程师"),
            (4, "产品经理"),
            (5, "数据分析师"),
            (6, "算法工程师"),
            (7, "测试工程师"),
        ],
    )
    def test_name_zh_matches(self, index: int, expected_zh: str) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        assert mod.SEED_ROWS[index][2] == expected_zh

    def test_sort_order_is_1_to_8(self) -> None:
        mod = _load_migration("007_seed_job_roles.py")
        sort_orders = [row[5] for row in mod.SEED_ROWS]
        assert sort_orders == list(range(1, 9))


class TestMigration007RevisionChain:
    """Verify full chain: None → 001 → ... → 007."""

    def test_full_chain_is_continuous(self) -> None:
        filenames = [
            "001_create_job_roles.py",
            "002_create_users.py",
            "003_create_refresh_tokens.py",
            "004_create_interview_sessions.py",
            "005_create_interview_messages.py",
            "006_create_interview_reports.py",
            "007_seed_job_roles.py",
        ]
        modules = [_load_migration(f) for f in filenames]

        assert modules[0].down_revision is None
        for i in range(1, len(modules)):
            assert modules[i].down_revision == modules[i - 1].revision
