"""Interview API — create, list, detail, start, messages, complete, cancel, transcribe."""

import math
import os
import uuid as _uuid
from uuid import UUID

from fastapi import APIRouter, Depends, File, Query, UploadFile
from fastapi.responses import Response as FastAPIResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import get_db
from app.models.interview_message import InterviewMessage
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
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
from app.schemas.report import ReportResponse, ReportStatusResponse
from app.services.interview_service import InterviewService
from app.services.openai_service import OpenAIService

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
            MessageResponse.model_validate(m).model_dump(by_alias=True) for m in session.messages
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
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

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
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    svc = InterviewService(db)
    session, question = await svc.start_session(sid, current_user.id)

    question_data = MessageResponse.model_validate(question).model_dump(by_alias=True)
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
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    svc = InterviewService(db)
    answer, next_question, is_finished, question_count = await svc.submit_answer(
        sid, current_user.id, body.content
    )

    response = SubmitAnswerResponse(
        answer=MessageResponse.model_validate(answer),
        next_question=(MessageResponse.model_validate(next_question) if next_question else None),
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
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

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
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    svc = InterviewService(db)
    session = await svc.cancel_session(sid, current_user.id)
    return _success(
        data=_session_to_response(session),
        message="面试已取消",
    )


# ---------------------------------------------------------------------------
# T027 — POST /interviews/{id}/transcribe — audio transcription
# ---------------------------------------------------------------------------

_ALLOWED_AUDIO_EXTENSIONS = {"webm", "mp3", "mp4", "m4a", "wav"}
_MAX_AUDIO_SIZE = 25 * 1024 * 1024  # 25 MB


@router.post("/{session_id}/transcribe", response_model=dict)
async def transcribe_audio(
    session_id: str,
    audio: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """POST /interviews/{id}/transcribe — upload audio and transcribe via Whisper."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    # Validate file size
    content = await audio.read()
    if len(content) > _MAX_AUDIO_SIZE:
        raise AppException(code=40003, message="文件大小超出限制", status_code=400)

    # Validate file extension
    filename = audio.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in _ALLOWED_AUDIO_EXTENSIONS:
        raise AppException(code=40004, message="不支持的文件格式", status_code=400)

    # Validate session ownership and status
    svc = InterviewService(db)
    session = await svc.get_session_detail(sid, current_user.id)
    if session.status != "in_progress":
        raise AppException(
            code=40901,
            message="操作与当前状态冲突",
            status_code=409,
        )

    # Save audio file to uploads/audio/{session_id}/{uuid}.{ext}
    upload_dir = os.path.join(settings.upload_dir, "audio", session_id)
    os.makedirs(upload_dir, exist_ok=True)
    unique_name = f"{_uuid.uuid4()}.{ext}"
    file_path = os.path.join(upload_dir, unique_name)
    with open(file_path, "wb") as f:
        f.write(content)

    # Call Whisper API
    openai_svc = OpenAIService()
    text = await openai_svc.transcribe_audio(file_path)

    audio_url = f"/api/v1/interviews/{session_id}/audio/{unique_name}"
    return _success(data={"text": text, "audioUrl": audio_url})


# ---------------------------------------------------------------------------
# T028 — GET /interviews/{id}/messages/{messageId}/tts — TTS audio
# ---------------------------------------------------------------------------


@router.get("/{session_id}/messages/{message_id}/tts")
async def get_message_tts(
    session_id: str,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FastAPIResponse:
    """GET /interviews/{id}/messages/{messageId}/tts — return TTS mp3 audio."""
    try:
        sid = UUID(session_id)
        mid = UUID(message_id)
    except ValueError:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    # Load session and validate ownership
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == sid))
    session = result.scalar_one_or_none()
    if session is None:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)
    if session.user_id != current_user.id:
        raise AppException(code=40301, message="无权访问该资源", status_code=403)

    # Validate voice mode
    if session.mode != "voice":
        raise AppException(code=40901, message="操作与当前状态冲突", status_code=409)

    # Load message and validate role
    result = await db.execute(
        select(InterviewMessage).where(
            InterviewMessage.id == mid,
            InterviewMessage.session_id == sid,
        )
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)
    if message.role != "interviewer":
        raise AppException(code=40901, message="操作与当前状态冲突", status_code=409)

    # Check TTS cache
    tts_dir = os.path.join(settings.upload_dir, "tts", session_id)
    tts_path = os.path.join(tts_dir, f"{message_id}.mp3")

    if not os.path.exists(tts_path):
        # Generate TTS via OpenAI
        openai_svc = OpenAIService()
        audio_bytes = await openai_svc.synthesize_speech(message.content)

        os.makedirs(tts_dir, exist_ok=True)
        with open(tts_path, "wb") as f:
            f.write(audio_bytes)

    with open(tts_path, "rb") as f:
        audio_data = f.read()

    return FastAPIResponse(content=audio_data, media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# T032 — GET /interviews/{id}/report/status — poll report generation status
# ---------------------------------------------------------------------------


@router.get("/{session_id}/report/status", response_model=dict)
async def get_report_status(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GET /interviews/{id}/report/status — return current report_status."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    # Load session and validate ownership
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == sid))
    session = result.scalar_one_or_none()
    if session is None:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)
    if session.user_id != current_user.id:
        raise AppException(code=40301, message="无权访问该资源", status_code=403)

    data = ReportStatusResponse(
        session_id=session.id,
        report_status=session.report_status,
    )
    return _success(data=data.model_dump(by_alias=True))


# ---------------------------------------------------------------------------
# T032 — GET /interviews/{id}/report — get the full report
# ---------------------------------------------------------------------------


@router.get("/{session_id}/report", response_model=dict)
async def get_report(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """GET /interviews/{id}/report — return the full report when ready."""
    try:
        sid = UUID(session_id)
    except ValueError:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)

    # Load session and validate ownership
    result = await db.execute(select(InterviewSession).where(InterviewSession.id == sid))
    session = result.scalar_one_or_none()
    if session is None:
        raise AppException(code=40403, message="面试会话不存在", status_code=404)
    if session.user_id != current_user.id:
        raise AppException(code=40301, message="无权访问该资源", status_code=403)

    # Report must be ready
    if session.report_status != "ready":
        raise AppException(
            code=40404,
            message="报告尚未生成完成",
            status_code=404,
        )

    # Load report
    result = await db.execute(select(InterviewReport).where(InterviewReport.session_id == sid))
    report = result.scalar_one_or_none()
    if report is None:
        raise AppException(
            code=40404,
            message="报告尚未生成完成",
            status_code=404,
        )

    data = ReportResponse.model_validate(report)
    return _success(data=data.model_dump(by_alias=True))
