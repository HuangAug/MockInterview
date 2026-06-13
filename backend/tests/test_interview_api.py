"""Tests for Interview API endpoints (T020-T023)."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.main import app
from app.models.interview_message import InterviewMessage
from app.models.interview_session import InterviewSession
from app.models.job_role import JobRole
from app.models.user import User

USER_UUID = uuid.UUID("b1000001-0000-4000-8000-000000000001")
SESSION_UUID = uuid.UUID("c1000001-0000-4000-8000-000000000001")
JOB_ROLE_UUID = uuid.UUID("a1000001-0000-4000-8000-000000000001")


def _mock_user() -> User:
    return User(
        id=USER_UUID,
        email="test@example.com",
        password_hash="hashed",
        display_name="TestUser",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


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
    report_status: str = "pending",
) -> InterviewSession:
    session = InterviewSession(
        id=SESSION_UUID,
        user_id=USER_UUID,
        job_role_id=JOB_ROLE_UUID,
        difficulty="mid",
        mode="text",
        status=status,
        question_count=question_count,
        max_questions=8,
        report_status=report_status,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    session.job_role = _mock_job_role()
    session.messages = []
    return session


def _mock_message(
    role: str = "interviewer",
    content: str = "请做一下自我介绍",
    sequence: int = 1,
) -> InterviewMessage:
    return InterviewMessage(
        id=uuid.uuid4(),
        session_id=SESSION_UUID,
        role=role,
        content=content,
        sequence=sequence,
        created_at=datetime.now(UTC),
    )


@pytest.fixture(autouse=True)
def reset_overrides() -> None:
    yield  # type: ignore[misc]
    app.dependency_overrides.clear()


def _setup_auth(mock_db: AsyncMock) -> None:
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: _mock_user()


# ===========================================================================
# T020 — POST /interviews (create)
# ===========================================================================


class TestCreateInterview:
    """POST /api/v1/interviews"""

    @pytest.mark.asyncio
    async def test_create_success_returns_201(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)
        session = _mock_session()

        with patch(
            "app.services.interview_service.InterviewService.create_session",
            new_callable=AsyncMock,
            return_value=session,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/interviews",
                    json={
                        "jobRoleId": str(JOB_ROLE_UUID),
                        "difficulty": "mid",
                        "mode": "text",
                    },
                )

        assert resp.status_code == 201
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "面试会话已创建"
        assert body["data"]["status"] == "pending"
        assert body["data"]["jobRoleName"] == "前端工程师"

    @pytest.mark.asyncio
    async def test_create_invalid_job_role_returns_40402(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.create_session",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40402, message="岗位不存在", status_code=404
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    "/api/v1/interviews",
                    json={
                        "jobRoleId": str(uuid.uuid4()),
                        "difficulty": "mid",
                        "mode": "text",
                    },
                )

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == 40402

    @pytest.mark.asyncio
    async def test_create_invalid_difficulty_returns_422(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/interviews",
                json={
                    "jobRoleId": str(JOB_ROLE_UUID),
                    "difficulty": "expert",
                    "mode": "text",
                },
            )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_requires_auth(self) -> None:
        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                "/api/v1/interviews",
                json={
                    "jobRoleId": str(JOB_ROLE_UUID),
                    "difficulty": "mid",
                    "mode": "text",
                },
            )

        assert resp.status_code == 403


# ===========================================================================
# T020 — GET /interviews (list)
# ===========================================================================


class TestListInterviews:
    """GET /api/v1/interviews"""

    @pytest.mark.asyncio
    async def test_list_returns_paginated_items(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        items = [
            {
                "id": SESSION_UUID,
                "jobRoleName": "前端工程师",
                "difficulty": "mid",
                "mode": "text",
                "status": "completed",
                "questionCount": 5,
                "reportStatus": "ready",
                "overallScore": 85.5,
                "createdAt": datetime.now(UTC),
            }
        ]

        with patch(
            "app.services.interview_service.InterviewService.list_sessions",
            new_callable=AsyncMock,
            return_value=(items, 1),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/interviews")

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert len(body["data"]["items"]) == 1
        assert body["data"]["pagination"]["total"] == 1
        assert body["data"]["pagination"]["page"] == 1

    @pytest.mark.asyncio
    async def test_list_empty(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.list_sessions",
            new_callable=AsyncMock,
            return_value=([], 0),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get("/api/v1/interviews")

        assert resp.status_code == 200
        assert resp.json()["data"]["items"] == []
        assert resp.json()["data"]["pagination"]["total"] == 0

    @pytest.mark.asyncio
    async def test_list_with_status_filter(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.list_sessions",
            new_callable=AsyncMock,
            return_value=([], 0),
        ) as mock_list:
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(
                    "/api/v1/interviews", params={"status": "completed"}
                )

        assert resp.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args.kwargs
        assert call_kwargs["status"] == "completed"


# ===========================================================================
# T020 — GET /interviews/{id} (detail)
# ===========================================================================


class TestGetInterview:
    """GET /api/v1/interviews/{id}"""

    @pytest.mark.asyncio
    async def test_detail_returns_session_with_messages(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        session = _mock_session(status="in_progress", question_count=2)
        session.messages = [
            _mock_message("interviewer", "请做一下自我介绍", 1),
            _mock_message("candidate", "我叫张三", 2),
            _mock_message("interviewer", "你有什么项目经验？", 3),
        ]

        with patch(
            "app.services.interview_service.InterviewService.get_session_detail",
            new_callable=AsyncMock,
            return_value=session,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(f"/api/v1/interviews/{SESSION_UUID}")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "in_progress"
        assert len(data["messages"]) == 3
        assert data["messages"][0]["role"] == "interviewer"

    @pytest.mark.asyncio
    async def test_detail_not_found_returns_40403(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.get_session_detail",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40403, message="面试会话不存在", status_code=404
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(f"/api/v1/interviews/{SESSION_UUID}")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == 40403

    @pytest.mark.asyncio
    async def test_detail_not_owner_returns_40301(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.get_session_detail",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40301, message="无权访问该资源", status_code=403
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.get(f"/api/v1/interviews/{SESSION_UUID}")

        assert resp.status_code == 403
        assert resp.json()["error"]["code"] == 40301

    @pytest.mark.asyncio
    async def test_detail_invalid_uuid_returns_40403(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.get("/api/v1/interviews/not-a-uuid")

        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == 40403


# ===========================================================================
# T021 — POST /interviews/{id}/start
# ===========================================================================


class TestStartInterview:
    """POST /api/v1/interviews/{id}/start"""

    @pytest.mark.asyncio
    async def test_start_returns_session_and_question(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        session = _mock_session(status="in_progress", question_count=1)
        question = _mock_message("interviewer", "请做一下自我介绍", 1)

        with patch(
            "app.services.interview_service.InterviewService.start_session",
            new_callable=AsyncMock,
            return_value=(session, question),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/start"
                )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["session"]["status"] == "in_progress"
        assert data["question"]["role"] == "interviewer"
        assert data["question"]["sequence"] == 1

    @pytest.mark.asyncio
    async def test_start_not_pending_returns_40903(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.start_session",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40903,
                message="面试会话状态不允许此操作",
                status_code=409,
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/start"
                )

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == 40903


# ===========================================================================
# T022 — POST /interviews/{id}/messages
# ===========================================================================


class TestSubmitAnswer:
    """POST /api/v1/interviews/{id}/messages"""

    @pytest.mark.asyncio
    async def test_submit_returns_answer_and_next_question(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        answer = _mock_message("candidate", "我叫张三", 2)
        next_q = _mock_message("interviewer", "你有什么项目经验？", 3)

        with patch(
            "app.services.interview_service.InterviewService.submit_answer",
            new_callable=AsyncMock,
            return_value=(answer, next_q, False, 2),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/messages",
                    json={"content": "我叫张三"},
                )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["answer"]["role"] == "candidate"
        assert data["nextQuestion"]["role"] == "interviewer"
        assert data["isFinished"] is False
        assert data["questionCount"] == 2

    @pytest.mark.asyncio
    async def test_submit_finished_returns_null_next_question(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        answer = _mock_message("candidate", "我的回答", 16)

        with patch(
            "app.services.interview_service.InterviewService.submit_answer",
            new_callable=AsyncMock,
            return_value=(answer, None, True, 8),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/messages",
                    json={"content": "我的回答"},
                )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["isFinished"] is True
        assert data["nextQuestion"] is None
        assert data["questionCount"] == 8

    @pytest.mark.asyncio
    async def test_submit_empty_content_returns_422(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"/api/v1/interviews/{SESSION_UUID}/messages",
                json={"content": ""},
            )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_not_in_progress_returns_40901(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.submit_answer",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40901, message="操作与当前状态冲突", status_code=409
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/messages",
                    json={"content": "some answer"},
                )

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == 40901


# ===========================================================================
# T023 — POST /interviews/{id}/complete
# ===========================================================================


class TestCompleteInterview:
    """POST /api/v1/interviews/{id}/complete"""

    @pytest.mark.asyncio
    async def test_complete_success(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        session = _mock_session(status="completed", question_count=3, report_status="generating")

        with patch(
            "app.services.interview_service.InterviewService.complete_session",
            new_callable=AsyncMock,
            return_value=session,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/complete"
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "面试已结束，正在生成报告"
        assert body["data"]["status"] == "completed"

    @pytest.mark.asyncio
    async def test_complete_zero_questions_returns_40901(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.complete_session",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40901, message="操作与当前状态冲突", status_code=409
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/complete"
                )

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == 40901


# ===========================================================================
# T023 — POST /interviews/{id}/cancel
# ===========================================================================


class TestCancelInterview:
    """POST /api/v1/interviews/{id}/cancel"""

    @pytest.mark.asyncio
    async def test_cancel_pending_success(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        session = _mock_session(status="cancelled")

        with patch(
            "app.services.interview_service.InterviewService.cancel_session",
            new_callable=AsyncMock,
            return_value=session,
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/cancel"
                )

        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["message"] == "面试已取消"
        assert body["data"]["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_with_questions_returns_40901(self) -> None:
        mock_db = AsyncMock()
        _setup_auth(mock_db)

        with patch(
            "app.services.interview_service.InterviewService.cancel_session",
            new_callable=AsyncMock,
            side_effect=AppException(
                code=40901, message="操作与当前状态冲突", status_code=409
            ),
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app), base_url="http://test"
            ) as client:
                resp = await client.post(
                    f"/api/v1/interviews/{SESSION_UUID}/cancel"
                )

        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == 40901
