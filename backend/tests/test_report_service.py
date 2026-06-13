"""Tests for ReportService async report generation (T034)."""

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.models.interview_report import InterviewReport
from app.services.report_service import ReportService

SESSION_UUID = uuid.UUID("c1000001-0000-4000-8000-000000000001")
JOB_ROLE_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")

_MOCK_REPORT_DATA = {
    "overallScore": 82,
    "communicationScore": 78,
    "technicalScore": 85,
    "problemSolvingScore": 80,
    "structureScore": 83,
    "strengths": ["表达清晰", "逻辑性强"],
    "weaknesses": ["项目经验不足"],
    "suggestions": ["多参与实战项目"],
    "questionFeedback": [
        {
            "sequence": 1,
            "question": "请做自我介绍",
            "answerSummary": "候选人介绍了教育背景和实习经历",
            "score": 80,
            "feedback": "回答结构清晰，可以更突出技术能力",
        }
    ],
    "summary": "候选人综合素质良好，技术基础扎实。",
}


def _mock_session() -> MagicMock:
    session = MagicMock()
    session.id = SESSION_UUID
    session.job_role_id = JOB_ROLE_UUID
    session.difficulty = "mid"
    session.question_count = 3
    session.report_status = "generating"
    return session


def _mock_job_role() -> MagicMock:
    jr = MagicMock()
    jr.id = JOB_ROLE_UUID
    jr.name_zh = "前端工程师"
    return jr


def _mock_message(seq: int) -> MagicMock:
    msg = MagicMock()
    msg.sequence = seq
    msg.role = "interviewer" if seq % 2 == 1 else "candidate"
    msg.content = f"Message {seq}"
    return msg


def _make_scalar_result(value: object) -> MagicMock:
    """Build a mock for db.execute() returning a scalar result."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = []
    result.scalars.return_value = scalars_mock
    return result


def _make_mock_db(
    session: MagicMock | None,
    job_role: MagicMock | None,
    messages: list[MagicMock] | None = None,
) -> AsyncMock:
    """Build a mock AsyncSession that returns the given entities.

    The execute side_effect covers:
      1. load session
      2. load job role (if session exists)
      3. load messages (if both exist)
      4. update report_status via _set_status (if reached)
    Extra calls beyond side_effect return a plain MagicMock.
    """
    mock_db = AsyncMock()

    results: list[MagicMock] = []

    # First query: load session
    session_result = _make_scalar_result(session)
    results.append(session_result)

    # Second query: load job role (only if session exists)
    if session is not None:
        jr_result = _make_scalar_result(job_role)
        results.append(jr_result)

        # If job_role not found → _set_status calls execute for UPDATE
        if job_role is None:
            results.append(MagicMock())  # update query

    # Third query: load messages (only if both exist)
    if session is not None and job_role is not None:
        msg_result = MagicMock()
        scalars_mock = MagicMock()
        scalars_mock.all.return_value = messages or []
        msg_result.scalars.return_value = scalars_mock
        results.append(msg_result)

        # Fourth query: update report_status via _set_status
        results.append(MagicMock())  # update query

    mock_db.execute = AsyncMock(side_effect=results)
    mock_db.flush = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    return mock_db


class _FakeSessionCtx:
    """Fake async context manager that yields the given mock_db."""

    def __init__(self, mock_db: AsyncMock) -> None:
        self._db = mock_db

    async def __aenter__(self) -> AsyncMock:
        return self._db

    async def __aexit__(self, *args: object) -> None:
        pass


def _make_session_context(mock_db: AsyncMock) -> _FakeSessionCtx:
    """Create an async context manager that yields mock_db."""
    return _FakeSessionCtx(mock_db)


# ---------------------------------------------------------------------------
# Tests: trigger_report_generation
# ---------------------------------------------------------------------------


class TestTriggerReportGeneration:
    """ReportService.trigger_report_generation"""

    def test_schedules_asyncio_task(self) -> None:
        with patch("app.services.report_service.asyncio.create_task") as mock_create:
            ReportService.trigger_report_generation(SESSION_UUID)
            mock_create.assert_called_once()
            # Close the unscheduled coroutine to avoid RuntimeWarning
            coro = mock_create.call_args[0][0]
            coro.close()


# ---------------------------------------------------------------------------
# Tests: _generate_report_task — success path
# ---------------------------------------------------------------------------


class TestGenerateReportTaskSuccess:
    """ReportService._generate_report_task — happy path"""

    @pytest.mark.asyncio
    async def test_report_written_to_db(self) -> None:
        session = _mock_session()
        job_role = _mock_job_role()
        messages = [_mock_message(1), _mock_message(2), _mock_message(3)]
        mock_db = _make_mock_db(session, job_role, messages)

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.OpenAIService"
            ) as MockOpenAI,
        ):
            mock_openai = AsyncMock()
            mock_openai.generate_report = AsyncMock(
                return_value=_MOCK_REPORT_DATA
            )
            MockOpenAI.return_value = mock_openai

            await ReportService._generate_report_task(SESSION_UUID)

        # Verify report was added to DB
        mock_db.add.assert_called_once()
        report = mock_db.add.call_args[0][0]
        assert isinstance(report, InterviewReport)
        assert report.session_id == SESSION_UUID
        assert report.overall_score == Decimal("82")
        assert report.communication_score == Decimal("78")
        assert report.technical_score == Decimal("85")
        assert report.problem_solving_score == Decimal("80")
        assert report.structure_score == Decimal("83")
        assert report.summary == "候选人综合素质良好，技术基础扎实。"

        # Verify commit
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_report_status_set_to_ready(self) -> None:
        session = _mock_session()
        job_role = _mock_job_role()
        mock_db = _make_mock_db(session, job_role, [])

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.OpenAIService"
            ) as MockOpenAI,
        ):
            mock_openai = AsyncMock()
            mock_openai.generate_report = AsyncMock(
                return_value=_MOCK_REPORT_DATA
            )
            MockOpenAI.return_value = mock_openai

            await ReportService._generate_report_task(SESSION_UUID)

        # Verify execute called for update (status → ready)
        # execute calls: session, job_role, messages, update
        assert mock_db.execute.call_count == 4
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_openai_called_with_correct_params(self) -> None:
        session = _mock_session()
        job_role = _mock_job_role()
        messages = [_mock_message(1), _mock_message(2)]
        mock_db = _make_mock_db(session, job_role, messages)

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.OpenAIService"
            ) as MockOpenAI,
        ):
            mock_openai = AsyncMock()
            mock_openai.generate_report = AsyncMock(
                return_value=_MOCK_REPORT_DATA
            )
            MockOpenAI.return_value = mock_openai

            await ReportService._generate_report_task(SESSION_UUID)

        mock_openai.generate_report.assert_called_once_with(
            job_role_name="前端工程师",
            difficulty="mid",
            question_count=3,
            messages=messages,
        )


# ---------------------------------------------------------------------------
# Tests: _generate_report_task — failure paths
# ---------------------------------------------------------------------------


class TestGenerateReportTaskFailure:
    """ReportService._generate_report_task — error handling"""

    @pytest.mark.asyncio
    async def test_session_not_found_no_crash(self) -> None:
        mock_db = _make_mock_db(None, None)

        with patch(
            "app.services.report_service.async_session_factory",
            return_value=_make_session_context(mock_db),
        ):
            # Should not raise
            await ReportService._generate_report_task(SESSION_UUID)

        # No report added, no commit
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_job_role_not_found_sets_failed(self) -> None:
        session = _mock_session()
        mock_db = _make_mock_db(session, None)

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.ReportService._safe_set_status",
                new_callable=AsyncMock,
            ) as mock_safe_set,
        ):
            await ReportService._generate_report_task(SESSION_UUID)

        # _set_status called within the main session (not _safe_set_status)
        # for the "failed" status update, flush should be called
        mock_db.flush.assert_called_once()

        # But also, when the function returns early, _safe_set_status
        # is NOT called (it's only called in except blocks).
        # The job_role not found path sets status via _set_status then returns.
        mock_safe_set.assert_not_called()

    @pytest.mark.asyncio
    async def test_openai_exception_sets_failed(self) -> None:
        session = _mock_session()
        job_role = _mock_job_role()
        messages = [_mock_message(1)]
        mock_db = _make_mock_db(session, job_role, messages)

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.OpenAIService"
            ) as MockOpenAI,
            patch(
                "app.services.report_service.ReportService._safe_set_status",
                new_callable=AsyncMock,
            ) as mock_safe_set,
        ):
            mock_openai = AsyncMock()
            mock_openai.generate_report = AsyncMock(
                side_effect=AppException(
                    code=50201,
                    message="AI 服务暂时不可用",
                    status_code=502,
                )
            )
            MockOpenAI.return_value = mock_openai

            await ReportService._generate_report_task(SESSION_UUID)

        # Report should NOT be added
        mock_db.add.assert_not_called()
        mock_db.commit.assert_not_called()

        # _safe_set_status should be called with "failed"
        mock_safe_set.assert_called_once_with(SESSION_UUID, "failed")

    @pytest.mark.asyncio
    async def test_unexpected_exception_sets_failed(self) -> None:
        session = _mock_session()
        job_role = _mock_job_role()
        mock_db = _make_mock_db(session, job_role, [])

        with (
            patch(
                "app.services.report_service.async_session_factory",
                return_value=_make_session_context(mock_db),
            ),
            patch(
                "app.services.report_service.OpenAIService"
            ) as MockOpenAI,
            patch(
                "app.services.report_service.ReportService._safe_set_status",
                new_callable=AsyncMock,
            ) as mock_safe_set,
        ):
            mock_openai = AsyncMock()
            mock_openai.generate_report = AsyncMock(
                side_effect=RuntimeError("unexpected")
            )
            MockOpenAI.return_value = mock_openai

            await ReportService._generate_report_task(SESSION_UUID)

        mock_db.add.assert_not_called()
        mock_safe_set.assert_called_once_with(SESSION_UUID, "failed")


# ---------------------------------------------------------------------------
# Tests: _set_status / _safe_set_status
# ---------------------------------------------------------------------------


class TestSetStatus:
    """ReportService._set_status and _safe_set_status"""

    @pytest.mark.asyncio
    async def test_set_status_executes_update_and_flush(self) -> None:
        mock_db = AsyncMock()
        await ReportService._set_status(mock_db, SESSION_UUID, "ready")

        mock_db.execute.assert_called_once()
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_set_status_creates_session_and_commits(self) -> None:
        mock_db = AsyncMock()

        with patch(
            "app.services.report_service.async_session_factory",
            return_value=_make_session_context(mock_db),
        ):
            await ReportService._safe_set_status(SESSION_UUID, "failed")

        mock_db.execute.assert_called_once()
        mock_db.flush.assert_called_once()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_safe_set_status_swallows_db_error(self) -> None:
        """_safe_set_status should not raise even if DB is unavailable."""
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(side_effect=RuntimeError("DB down"))

        with patch(
            "app.services.report_service.async_session_factory",
            return_value=_make_session_context(mock_db),
        ):
            # Should not raise
            await ReportService._safe_set_status(SESSION_UUID, "failed")


# ---------------------------------------------------------------------------
# Tests: complete_session integration with trigger_report_generation
# ---------------------------------------------------------------------------


class TestCompleteSessionTriggersReport:
    """Verify complete_session calls ReportService.trigger_report_generation."""

    @pytest.mark.asyncio
    async def test_complete_session_triggers_report(self) -> None:
        from app.services.interview_service import InterviewService

        mock_db = AsyncMock()

        session = MagicMock()
        session.id = SESSION_UUID
        session.user_id = uuid.UUID("b1000001-0000-4000-8000-000000000001")
        session.status = "in_progress"
        session.question_count = 3
        session.job_role_id = JOB_ROLE_UUID

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_scalar_result(session),  # get session
                None,  # update
                _make_scalar_result(session),  # reload
            ]
        )
        mock_db.flush = AsyncMock()

        with patch(
            "app.services.interview_service.ReportService.trigger_report_generation"
        ) as mock_trigger:
            svc = InterviewService(mock_db)
            await svc.complete_session(
                SESSION_UUID,
                uuid.UUID("b1000001-0000-4000-8000-000000000001"),
            )

        mock_trigger.assert_called_once_with(SESSION_UUID)
