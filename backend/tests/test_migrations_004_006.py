"""Tests for database migration files 004-006 (interview_sessions, messages, reports)."""

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


class TestMigrationFilesExist004to006:
    """All three migration files must exist."""

    @pytest.mark.parametrize(
        "filename",
        [
            "004_create_interview_sessions.py",
            "005_create_interview_messages.py",
            "006_create_interview_reports.py",
        ],
    )
    def test_migration_file_exists(self, filename: str) -> None:
        assert (MIGRATIONS_DIR / filename).is_file()


class TestMigration004InterviewSessions:
    """Verify interview_sessions migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("004_create_interview_sessions.py")
        assert mod.revision == "004"

    def test_down_revision_is_003(self) -> None:
        mod = _load_migration("004_create_interview_sessions.py")
        assert mod.down_revision == "003"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("004_create_interview_sessions.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("004_create_interview_sessions.py")
        assert callable(mod.downgrade)


class TestMigration005InterviewMessages:
    """Verify interview_messages migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("005_create_interview_messages.py")
        assert mod.revision == "005"

    def test_down_revision_is_004(self) -> None:
        mod = _load_migration("005_create_interview_messages.py")
        assert mod.down_revision == "004"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("005_create_interview_messages.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("005_create_interview_messages.py")
        assert callable(mod.downgrade)


class TestMigration006InterviewReports:
    """Verify interview_reports migration revision chain and structure."""

    def test_revision_id(self) -> None:
        mod = _load_migration("006_create_interview_reports.py")
        assert mod.revision == "006"

    def test_down_revision_is_005(self) -> None:
        mod = _load_migration("006_create_interview_reports.py")
        assert mod.down_revision == "005"

    def test_upgrade_function_exists(self) -> None:
        mod = _load_migration("006_create_interview_reports.py")
        assert callable(mod.upgrade)

    def test_downgrade_function_exists(self) -> None:
        mod = _load_migration("006_create_interview_reports.py")
        assert callable(mod.downgrade)


class TestMigrationRevisionChain004to006:
    """Verify the revision chain: 003 → 004 → 005 → 006."""

    def test_revision_chain_is_continuous(self) -> None:
        m003 = _load_migration("003_create_refresh_tokens.py")
        m004 = _load_migration("004_create_interview_sessions.py")
        m005 = _load_migration("005_create_interview_messages.py")
        m006 = _load_migration("006_create_interview_reports.py")

        assert m004.down_revision == m003.revision
        assert m005.down_revision == m004.revision
        assert m006.down_revision == m005.revision


class TestMigration004CheckConstraints:
    """Verify CHECK constraint names in interview_sessions migration."""

    def test_has_difficulty_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_difficulty" in source
        assert "'junior'" in source and "'mid'" in source and "'senior'" in source

    def test_has_mode_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_mode" in source
        assert "'text'" in source and "'voice'" in source

    def test_has_status_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_status" in source
        assert "'pending'" in source and "'completed'" in source and "'cancelled'" in source

    def test_has_report_status_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_report_status" in source
        assert "'generating'" in source and "'ready'" in source and "'failed'" in source

    def test_has_question_count_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_question_count" in source
        assert "question_count >= 0" in source

    def test_has_max_questions_check(self) -> None:
        source = (MIGRATIONS_DIR / "004_create_interview_sessions.py").read_text()
        assert "chk_sessions_max_questions" in source
        assert "max_questions > 0" in source


class TestMigration005UniqueConstraint:
    """Verify UNIQUE(session_id, sequence) in interview_messages."""

    def test_has_session_sequence_unique(self) -> None:
        source = (MIGRATIONS_DIR / "005_create_interview_messages.py").read_text()
        assert "uq_messages_session_sequence" in source
        assert '"session_id"' in source and '"sequence"' in source


class TestMigration006ReportConstraints:
    """Verify UNIQUE(session_id) and score CHECK constraints in interview_reports."""

    def test_has_session_id_unique(self) -> None:
        source = (MIGRATIONS_DIR / "006_create_interview_reports.py").read_text()
        assert "uq_reports_session_id" in source

    @pytest.mark.parametrize(
        "constraint_name",
        [
            "chk_reports_overall_score",
            "chk_reports_communication_score",
            "chk_reports_technical_score",
            "chk_reports_problem_solving_score",
            "chk_reports_structure_score",
        ],
    )
    def test_has_score_check_constraints(self, constraint_name: str) -> None:
        source = (MIGRATIONS_DIR / "006_create_interview_reports.py").read_text()
        assert constraint_name in source

    def test_uses_jsonb_for_json_columns(self) -> None:
        source = (MIGRATIONS_DIR / "006_create_interview_reports.py").read_text()
        assert "postgresql.JSONB" in source
