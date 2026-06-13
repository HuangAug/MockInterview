"""Tests for InterviewService state machine (T019)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import AppException
from app.models.interview_message import InterviewMessage
from app.models.interview_session import InterviewSession
from app.models.job_role import JobRole
from app.services.interview_service import InterviewService

USER_UUID = uuid.UUID("b1000001-0000-4000-8000-000000000001")
OTHER_USER_UUID = uuid.UUID("b2000001-0000-4000-8000-000000000001")
SESSION_UUID = uuid.UUID("c1000001-0000-4000-8000-000000000001")
JOB_ROLE_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


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


def _mock_session(
    status: str = "pending",
    question_count: int = 0,
    user_id: uuid.UUID = USER_UUID,
    max_questions: int = 8,
) -> InterviewSession:
    return InterviewSession(
        id=SESSION_UUID,
        user_id=user_id,
        job_role_id=JOB_ROLE_UUID,
        difficulty="mid",
        mode="text",
        status=status,
        question_count=question_count,
        max_questions=max_questions,
        report_status="pending",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _make_result(scalar: object | None) -> MagicMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = scalar
    mock_result.scalar_one.return_value = scalar
    mock_result.scalar.return_value = scalar
    return mock_result


def _make_session_result(session: InterviewSession) -> MagicMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = session
    mock_result.scalar_one.return_value = session
    return mock_result


class TestCreateSession:
    """InterviewService.create_session"""

    @pytest.mark.asyncio
    async def test_create_session_success(self) -> None:
        mock_db = AsyncMock()
        mock_openai = AsyncMock()

        # DB calls: 1) validate job role, 2) flush, 3) reload session
        jr = _mock_job_role()
        session = _mock_session()

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_result(jr),  # validate job role
                _make_session_result(session),  # reload
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = InterviewService(mock_db, openai=mock_openai)
        result = await svc.create_session(
            USER_UUID, JOB_ROLE_UUID, "mid", "text"
        )

        mock_db.add.assert_called_once()
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_create_session_invalid_job_role(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.create_session(USER_UUID, uuid.uuid4(), "mid", "text")

        assert exc_info.value.code == 40402


class TestStartSession:
    """InterviewService.start_session — pending → in_progress"""

    @pytest.mark.asyncio
    async def test_start_session_success(self) -> None:
        mock_db = AsyncMock()
        mock_openai = AsyncMock()
        mock_openai.generate_first_question = AsyncMock(
            return_value="请做一下自我介绍"
        )

        session = _mock_session(status="pending")

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                _make_result(_mock_job_role()),  # load job role
                None,  # update session
                _make_session_result(session),  # reload session
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = InterviewService(mock_db, openai=mock_openai)
        result_session, question = await svc.start_session(SESSION_UUID, USER_UUID)

        assert question.role == "interviewer"
        assert question.sequence == 1
        assert question.content == "请做一下自我介绍"
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_not_pending_raises_40903(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress")
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.start_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40903

    @pytest.mark.asyncio
    async def test_start_wrong_user_raises_40301(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="pending", user_id=OTHER_USER_UUID)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.start_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40301

    @pytest.mark.asyncio
    async def test_start_not_found_raises_40403(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.start_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40403


class TestSubmitAnswer:
    """InterviewService.submit_answer"""

    @pytest.mark.asyncio
    async def test_submit_answer_generates_next_question(self) -> None:
        mock_db = AsyncMock()
        mock_openai = AsyncMock()
        mock_openai.generate_next_question = AsyncMock(
            return_value=("你有什么项目经验？", False)
        )

        session = _mock_session(status="in_progress", question_count=1)
        candidate_msg = InterviewMessage(
            session_id=SESSION_UUID, role="candidate", content="我叫张三", sequence=2,
        )
        interviewer_msg = InterviewMessage(
            session_id=SESSION_UUID, role="interviewer", content="你有什么项目经验？", sequence=3,
        )

        # Mock the max sequence query and messages query
        max_seq_result = MagicMock()
        max_seq_result.scalar_one_or_none.return_value = 1
        max_seq_result.scalar_one.return_value = 1
        max_seq_result.scalar.return_value = 1

        messages_result = MagicMock()
        messages_scalars = MagicMock()
        messages_scalars.all.return_value = []
        messages_result.scalars.return_value = messages_scalars

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                max_seq_result,  # max sequence
                _make_result(_mock_job_role()),  # load job role
                messages_result,  # load messages
                None,  # update question_count
                _make_session_result(session),  # (not called in this path)
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = InterviewService(mock_db, openai=mock_openai)
        answer, next_q, is_finished, count = await svc.submit_answer(
            SESSION_UUID, USER_UUID, "我叫张三"
        )

        assert answer.role == "candidate"
        assert answer.sequence == 2
        assert next_q is not None
        assert next_q.role == "interviewer"
        assert next_q.sequence == 3
        assert is_finished is False
        assert count == 2

    @pytest.mark.asyncio
    async def test_submit_answer_max_questions_reached(self) -> None:
        mock_db = AsyncMock()
        mock_openai = AsyncMock()

        session = _mock_session(status="in_progress", question_count=8, max_questions=8)

        max_seq_result = MagicMock()
        max_seq_result.scalar_one_or_none.return_value = 15
        max_seq_result.scalar_one.return_value = 15
        max_seq_result.scalar.return_value = 15

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                max_seq_result,  # max sequence
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = InterviewService(mock_db, openai=mock_openai)
        answer, next_q, is_finished, count = await svc.submit_answer(
            SESSION_UUID, USER_UUID, "我的回答"
        )

        assert answer.role == "candidate"
        assert next_q is None
        assert is_finished is True
        assert count == 8
        mock_openai.generate_next_question.assert_not_called()

    @pytest.mark.asyncio
    async def test_submit_answer_llm_signals_complete(self) -> None:
        mock_db = AsyncMock()
        mock_openai = AsyncMock()
        mock_openai.generate_next_question = AsyncMock(
            return_value=("", True)
        )

        session = _mock_session(status="in_progress", question_count=3)

        max_seq_result = MagicMock()
        max_seq_result.scalar_one_or_none.return_value = 6
        max_seq_result.scalar_one.return_value = 6
        max_seq_result.scalar.return_value = 6

        messages_result = MagicMock()
        messages_scalars = MagicMock()
        messages_scalars.all.return_value = []
        messages_result.scalars.return_value = messages_scalars

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                max_seq_result,  # max sequence
                _make_result(_mock_job_role()),  # load job role
                messages_result,  # load messages
            ]
        )
        mock_db.flush = AsyncMock()
        mock_db.add = MagicMock()

        svc = InterviewService(mock_db, openai=mock_openai)
        answer, next_q, is_finished, count = await svc.submit_answer(
            SESSION_UUID, USER_UUID, "我的回答"
        )

        assert next_q is None
        assert is_finished is True
        assert count == 3

    @pytest.mark.asyncio
    async def test_submit_answer_not_in_progress_raises_40901(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="completed")
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.submit_answer(SESSION_UUID, USER_UUID, "answer")

        assert exc_info.value.code == 40901

    @pytest.mark.asyncio
    async def test_submit_answer_wrong_user_raises_40301(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress", user_id=OTHER_USER_UUID)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.submit_answer(SESSION_UUID, USER_UUID, "answer")

        assert exc_info.value.code == 40301


class TestCompleteSession:
    """InterviewService.complete_session — in_progress → completed"""

    @pytest.mark.asyncio
    async def test_complete_success(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress", question_count=3)

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                None,  # update
                _make_session_result(session),  # reload
            ]
        )
        mock_db.flush = AsyncMock()

        svc = InterviewService(mock_db)
        result = await svc.complete_session(SESSION_UUID, USER_UUID)

        # Verify update was called
        assert mock_db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_complete_not_in_progress_raises_40903(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="pending")
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.complete_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40903

    @pytest.mark.asyncio
    async def test_complete_zero_questions_raises_40901(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress", question_count=0)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.complete_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40901

    @pytest.mark.asyncio
    async def test_complete_already_completed_raises_40903(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="completed", question_count=3)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.complete_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40903


class TestCancelSession:
    """InterviewService.cancel_session"""

    @pytest.mark.asyncio
    async def test_cancel_pending_session(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="pending")

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),  # get session
                None,  # update
                _make_session_result(session),  # reload
            ]
        )
        mock_db.flush = AsyncMock()

        svc = InterviewService(mock_db)
        result = await svc.cancel_session(SESSION_UUID, USER_UUID)

        assert mock_db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_cancel_in_progress_zero_questions(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress", question_count=0)

        mock_db.execute = AsyncMock(
            side_effect=[
                _make_session_result(session),
                None,
                _make_session_result(session),
            ]
        )
        mock_db.flush = AsyncMock()

        svc = InterviewService(mock_db)
        result = await svc.cancel_session(SESSION_UUID, USER_UUID)

        assert mock_db.execute.call_count == 3

    @pytest.mark.asyncio
    async def test_cancel_in_progress_with_questions_raises_40901(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="in_progress", question_count=3)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.cancel_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40901

    @pytest.mark.asyncio
    async def test_cancel_completed_raises_40903(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="completed", question_count=3)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.cancel_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40903

    @pytest.mark.asyncio
    async def test_cancel_wrong_user_raises_40301(self) -> None:
        mock_db = AsyncMock()
        session = _mock_session(status="pending", user_id=OTHER_USER_UUID)
        mock_db.execute = AsyncMock(
            return_value=_make_session_result(session)
        )

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.cancel_session(SESSION_UUID, USER_UUID)

        assert exc_info.value.code == 40301


class TestSessionNotFound:
    """All operations should raise 40403 when session not found."""

    @pytest.mark.asyncio
    async def test_start_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.start_session(uuid.uuid4(), USER_UUID)
        assert exc_info.value.code == 40403

    @pytest.mark.asyncio
    async def test_submit_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.submit_answer(uuid.uuid4(), USER_UUID, "text")
        assert exc_info.value.code == 40403

    @pytest.mark.asyncio
    async def test_complete_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.complete_session(uuid.uuid4(), USER_UUID)
        assert exc_info.value.code == 40403

    @pytest.mark.asyncio
    async def test_cancel_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.cancel_session(uuid.uuid4(), USER_UUID)
        assert exc_info.value.code == 40403

    @pytest.mark.asyncio
    async def test_detail_not_found(self) -> None:
        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=_make_result(None))

        svc = InterviewService(mock_db)
        with pytest.raises(AppException) as exc_info:
            await svc.get_session_detail(uuid.uuid4(), USER_UUID)
        assert exc_info.value.code == 40403
