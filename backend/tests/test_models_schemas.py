"""Tests for SQLAlchemy Models and Pydantic Schemas (T009)."""

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

# ─── Model Tests ─────────────────────────────────────────────────────────────


class TestModelsImport:
    """All 6 models must be importable from app.models."""

    def test_import_user(self) -> None:
        from app.models.user import User

        assert User.__tablename__ == "users"

    def test_import_refresh_token(self) -> None:
        from app.models.refresh_token import RefreshToken

        assert RefreshToken.__tablename__ == "refresh_tokens"

    def test_import_job_role(self) -> None:
        from app.models.job_role import JobRole

        assert JobRole.__tablename__ == "job_roles"

    def test_import_interview_session(self) -> None:
        from app.models.interview_session import InterviewSession

        assert InterviewSession.__tablename__ == "interview_sessions"

    def test_import_interview_message(self) -> None:
        from app.models.interview_message import InterviewMessage

        assert InterviewMessage.__tablename__ == "interview_messages"

    def test_import_interview_report(self) -> None:
        from app.models.interview_report import InterviewReport

        assert InterviewReport.__tablename__ == "interview_reports"


class TestModelRelationships:
    """Verify relationship attributes exist on each model."""

    def test_user_has_refresh_tokens_rel(self) -> None:
        from app.models.user import User

        assert hasattr(User, "refresh_tokens")

    def test_user_has_interview_sessions_rel(self) -> None:
        from app.models.user import User

        assert hasattr(User, "interview_sessions")

    def test_user_has_target_job_role_rel(self) -> None:
        from app.models.user import User

        assert hasattr(User, "target_job_role")

    def test_session_has_messages_rel(self) -> None:
        from app.models.interview_session import InterviewSession

        assert hasattr(InterviewSession, "messages")

    def test_session_has_report_rel(self) -> None:
        from app.models.interview_session import InterviewSession

        assert hasattr(InterviewSession, "report")

    def test_report_has_session_rel(self) -> None:
        from app.models.interview_report import InterviewReport

        assert hasattr(InterviewReport, "session")


# ─── Schema Tests ────────────────────────────────────────────────────────────

FIXED_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")
NOW = datetime(2026, 6, 12, 10, 0, 0, tzinfo=UTC)


class TestAuthSchemas:
    """Verify auth request/response schemas."""

    def test_register_request_accepts_valid(self) -> None:
        from app.schemas.auth import RegisterRequest

        req = RegisterRequest(
            email="test@example.com", password="Pass1234", display_name="Test"
        )
        assert req.email == "test@example.com"

    def test_register_request_camel_alias(self) -> None:
        from app.schemas.auth import RegisterRequest

        req = RegisterRequest.model_validate(
            {"email": "a@b.com", "password": "Pass1234", "displayName": "X"}
        )
        assert req.display_name == "X"

    def test_token_response_defaults(self) -> None:
        from app.schemas.auth import TokenResponse

        t = TokenResponse(access_token="at", refresh_token="rt")
        assert t.token_type == "Bearer"
        assert t.expires_in == 900

    def test_token_response_camel_output(self) -> None:
        from app.schemas.auth import TokenResponse

        t = TokenResponse(access_token="at", refresh_token="rt")
        dumped = t.model_dump(by_alias=True)
        assert "accessToken" in dumped
        assert "refreshToken" in dumped


class TestUserSchemas:
    """Verify user response and update schemas."""

    def test_user_response_from_dict(self) -> None:
        from app.schemas.user import UserResponse

        u = UserResponse(
            id=FIXED_UUID,
            email="a@b.com",
            display_name="Test",
            created_at=NOW,
        )
        assert u.email == "a@b.com"
        assert u.target_job_role_id is None

    def test_update_user_request_partial(self) -> None:
        from app.schemas.user import UpdateUserRequest

        req = UpdateUserRequest(display_name="New")
        assert req.display_name == "New"
        assert req.target_job_role_id is None

    def test_update_user_rejects_empty_display_name(self) -> None:
        from app.schemas.user import UpdateUserRequest

        with pytest.raises(ValidationError):
            UpdateUserRequest(display_name="")


class TestJobRoleSchemas:
    """Verify job role response schema."""

    def test_job_role_response(self) -> None:
        from app.schemas.job_role import JobRoleResponse

        jr = JobRoleResponse(
            id=FIXED_UUID,
            code="frontend",
            name_zh="前端工程师",
            name_en="Frontend Engineer",
            description="desc",
            sort_order=1,
        )
        dumped = jr.model_dump(by_alias=True)
        assert dumped["nameZh"] == "前端工程师"
        assert dumped["nameEn"] == "Frontend Engineer"
        assert dumped["sortOrder"] == 1


class TestInterviewSchemas:
    """Verify interview request/response schemas."""

    def test_create_interview_request(self) -> None:
        from app.schemas.interview import CreateInterviewRequest

        req = CreateInterviewRequest(
            job_role_id=FIXED_UUID, difficulty="mid", mode="text"
        )
        assert req.difficulty == "mid"

    def test_create_interview_rejects_invalid_difficulty(self) -> None:
        from app.schemas.interview import CreateInterviewRequest

        with pytest.raises(ValidationError):
            CreateInterviewRequest(
                job_role_id=FIXED_UUID, difficulty="expert", mode="text"  # type: ignore[arg-type]
            )

    def test_message_response(self) -> None:
        from app.schemas.interview import MessageResponse

        m = MessageResponse(
            id=FIXED_UUID,
            session_id=FIXED_UUID,
            role="interviewer",
            content="Tell me about yourself.",
            sequence=1,
            created_at=NOW,
        )
        dumped = m.model_dump(by_alias=True)
        assert "sessionId" in dumped
        assert dumped["sequence"] == 1

    def test_submit_answer_request_max_length(self) -> None:
        from app.schemas.interview import SubmitAnswerRequest

        with pytest.raises(ValidationError):
            SubmitAnswerRequest(content="x" * 5001)

    def test_submit_answer_response(self) -> None:
        from app.schemas.interview import MessageResponse, SubmitAnswerResponse

        msg = MessageResponse(
            id=FIXED_UUID,
            session_id=FIXED_UUID,
            role="candidate",
            content="My answer",
            sequence=2,
            created_at=NOW,
        )
        resp = SubmitAnswerResponse(
            answer=msg, is_finished=False, question_count=2
        )
        dumped = resp.model_dump(by_alias=True)
        assert dumped["isFinished"] is False
        assert dumped["questionCount"] == 2


class TestReportSchemas:
    """Verify report response schemas."""

    def test_report_response(self) -> None:
        from app.schemas.report import QuestionFeedbackItem, ReportResponse

        qf = QuestionFeedbackItem(
            sequence=1,
            question="Q1",
            answer_summary="Short",
            score=80.0,
            feedback="Good",
        )
        r = ReportResponse(
            id=FIXED_UUID,
            session_id=FIXED_UUID,
            overall_score=85.5,
            communication_score=80.0,
            technical_score=90.0,
            problem_solving_score=85.0,
            structure_score=88.0,
            strengths=["Clear"],
            weaknesses=["Slow"],
            suggestions=["Practice"],
            question_feedback=[qf],
            summary="Good interview.",
            created_at=NOW,
        )
        dumped = r.model_dump(by_alias=True)
        assert dumped["overallScore"] == 85.5
        assert len(dumped["questionFeedback"]) == 1
        assert dumped["questionFeedback"][0]["answerSummary"] == "Short"

    def test_report_status_response(self) -> None:
        from app.schemas.report import ReportStatusResponse

        rs = ReportStatusResponse(session_id=FIXED_UUID, report_status="generating")
        dumped = rs.model_dump(by_alias=True)
        assert dumped["reportStatus"] == "generating"
        assert "sessionId" in dumped
