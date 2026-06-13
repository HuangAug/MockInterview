"""Interview API — create, list, detail, start, messages, complete, cancel."""

import math
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.user import User
from app.schemas.interview import (
    CreateInterviewRequest,
    InterviewSessionResponse,
    MessageResponse,
    PaginationMeta,
    PaginationResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.interview_service import InterviewService

router = APIRouter(prefix="/interviews", tags=["interviews"])


def _success(data: dict | None, message: str | None = None) -> dict:
    """Build the unified success response envelope."""
    return {"success": True, "data": data, "message": message}


def _session_to_response(session: object) -> dict:
    """Convert an InterviewSession (with loaded job_role) to response dict."""
    job_role_name = None
    if hasattr(session, "job_role") and session.job_role is not None:
        job_role_name = session.job_role.name_zh

    messages = None
    if hasattr(session, "messages") and session.messages is not None:
        messages = [
            MessageResponse.model_validate(m).model_dump(by_alias=True)
            for m in session.messages
        ]

    return InterviewSessionResponse(
        id=session.id,
        job_role_id=session.job_role_id,
        job_role_name=job_role_name,
        difficulty=session.difficulty,
        mode=session.mode,
        status=session.status,
        question_count=session.question_count,
        max_questions=session.max_questions,
        report_status=session.report_status,
        started_at=session.started_at,
        ended_at=session.ended_at,
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=messages,
    ).model_dump(by_alias=True)


# ---------------------------------------------------------------------------
# T020 — POST /interviews — create session
# ---------------------------------------------------------------------------


@router.post("", response_model=dict, status_code=201)
async def create_interview(
    body: CreateInterviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews — create a new interview session."""
    svc = InterviewService(db)
    session = await svc.create_session(
        user_id=current_user.id,
        job_role_id=body.job_role_id,
        difficulty=body.difficulty,
        mode=body.mode,
    )
    return _success(
        data=_session_to_response(session),
        message="面试会话已创建",
    )


# ---------------------------------------------------------------------------
# T020 — GET /interviews — list user's sessions (paginated)
# ---------------------------------------------------------------------------


@router.get("", response_model=dict)
async def list_interviews(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=50),
    status: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GET /interviews — paginated list of current user's interview sessions."""
    svc = InterviewService(db)
    items, total = await svc.list_sessions(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        status=status,
    )
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    pagination = PaginationMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
    result = PaginationResponse(
        items=[],  # items are already dicts with camelCase keys
        pagination=pagination,
    )
    # Replace the empty items list with pre-formatted dicts
    response_data = result.model_dump(by_alias=True)
    response_data["items"] = items

    return _success(data=response_data)


# ---------------------------------------------------------------------------
# T020 — GET /interviews/{id} — session detail with messages
# ---------------------------------------------------------------------------


@router.get("/{session_id}", response_model=dict)
async def get_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GET /interviews/{id} — session detail with all messages."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(
            code=40403, message="面试会话不存在", status_code=404
        )

    svc = InterviewService(db)
    session = await svc.get_session_detail(sid, current_user.id)
    return _success(data=_session_to_response(session))


# ---------------------------------------------------------------------------
# T021 — POST /interviews/{id}/start — start interview
# ---------------------------------------------------------------------------


@router.post("/{session_id}/start", response_model=dict)
async def start_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews/{id}/start — generate first question, begin interview."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(
            code=40403, message="面试会话不存在", status_code=404
        )

    svc = InterviewService(db)
    session, question = await svc.start_session(sid, current_user.id)

    question_data = MessageResponse.model_validate(question).model_dump(
        by_alias=True
    )
    return _success(
        data={
            "session": _session_to_response(session),
            "question": question_data,
        }
    )


# ---------------------------------------------------------------------------
# T022 — POST /interviews/{id}/messages — submit answer
# ---------------------------------------------------------------------------


@router.post("/{session_id}/messages", response_model=dict)
async def submit_answer(
    session_id: str,
    body: SubmitAnswerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews/{id}/messages — submit candidate answer, get next question."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(
            code=40403, message="面试会话不存在", status_code=404
        )

    svc = InterviewService(db)
    answer, next_question, is_finished, question_count = await svc.submit_answer(
        sid, current_user.id, body.content
    )

    response = SubmitAnswerResponse(
        answer=MessageResponse.model_validate(answer),
        next_question=(
            MessageResponse.model_validate(next_question)
            if next_question
            else None
        ),
        is_finished=is_finished,
        question_count=question_count,
    )
    return _success(data=response.model_dump(by_alias=True))


# ---------------------------------------------------------------------------
# T023 — POST /interviews/{id}/complete — complete interview
# ---------------------------------------------------------------------------


@router.post("/{session_id}/complete", response_model=dict)
async def complete_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews/{id}/complete — end interview, trigger report generation."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(
            code=40403, message="面试会话不存在", status_code=404
        )

    svc = InterviewService(db)
    session = await svc.complete_session(sid, current_user.id)
    return _success(
        data=_session_to_response(session),
        message="面试已结束，正在生成报告",
    )


# ---------------------------------------------------------------------------
# T023 — POST /interviews/{id}/cancel — cancel interview
# ---------------------------------------------------------------------------


@router.post("/{session_id}/cancel", response_model=dict)
async def cancel_interview(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews/{id}/cancel — cancel the interview."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(
            code=40403, message="面试会话不存在", status_code=404
        )

    svc = InterviewService(db)
    session = await svc.cancel_session(sid, current_user.id)
    return _success(
        data=_session_to_response(session),
        message="面试已取消",
    )
