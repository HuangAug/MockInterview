"""InterviewService — business logic for interview session state machine."""

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import AppException
from app.models.interview_message import InterviewMessage
from app.models.interview_session import InterviewSession
from app.models.job_role import JobRole
from app.services.openai_service import OpenAIService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)


class InterviewService:
    """Handles interview session state machine and message management."""

    def __init__(self, db: AsyncSession, openai: OpenAIService | None = None) -> None:
        self._db = db
        self._openai = openai or OpenAIService()

    # -------------------------------------------------------------------------
    # Create session
    # -------------------------------------------------------------------------

    async def create_session(
        self,
        user_id: UUID,
        job_role_id: UUID,
        difficulty: str,
        mode: str,
    ) -> InterviewSession:
        """Create a new interview session in pending state.

        Raises:
            AppException(40402): jobRoleId is invalid or inactive.
        """
        # Validate job role
        result = await self._db.execute(
            select(JobRole).where(
                JobRole.id == job_role_id, JobRole.is_active.is_(True)
            )
        )
        if result.scalar_one_or_none() is None:
            raise AppException(code=40402, message="岗位不存在", status_code=404)

        session = InterviewSession(
            user_id=user_id,
            job_role_id=job_role_id,
            difficulty=difficulty,
            mode=mode,
        )
        self._db.add(session)
        await self._db.flush()

        # Eagerly load relationships for response
        return await self._load_session_with_relations(session.id)

    # -------------------------------------------------------------------------
    # Start session — pending → in_progress
    # -------------------------------------------------------------------------

    async def start_session(
        self, session_id: UUID, user_id: UUID
    ) -> tuple[InterviewSession, InterviewMessage]:
        """Start the interview: generate first question, transition to in_progress.

        Returns:
            (session, first_question_message)

        Raises:
            AppException(40403): Session not found.
            AppException(40301): Session does not belong to current user.
            AppException(40903): Session is not in pending state.
            AppException(50201): OpenAI call failed.
        """
        session = await self._get_session_or_404(session_id)
        self._check_ownership(session, user_id)

        if session.status != "pending":
            raise AppException(
                code=40903,
                message="面试会话状态不允许此操作",
                status_code=409,
            )

        # Load job role for name
        job_role = await self._load_job_role(session.job_role_id)

        # Generate first question
        question_text = await self._openai.generate_first_question(
            job_role_name=job_role.name_zh,
            difficulty=session.difficulty,
            max_questions=session.max_questions,
        )

        # Insert interviewer message (sequence=1)
        message = InterviewMessage(
            session_id=session_id,
            role="interviewer",
            content=question_text,
            sequence=1,
        )
        self._db.add(message)

        # Update session state
        now = datetime.now(UTC)
        await self._db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(
                status="in_progress",
                question_count=1,
                started_at=now,
                updated_at=now,
            )
        )
        await self._db.flush()

        # Reload session for response
        session = await self._load_session_with_relations(session_id)
        return session, message

    # -------------------------------------------------------------------------
    # Submit answer — stores candidate message, generates next question
    # -------------------------------------------------------------------------

    async def submit_answer(
        self, session_id: UUID, user_id: UUID, content: str
    ) -> tuple[InterviewMessage, InterviewMessage | None, bool, int]:
        """Submit a candidate answer and optionally generate the next question.

        Returns:
            (answer_message, next_question_or_none, is_finished, question_count)

        Raises:
            AppException(40403): Session not found.
            AppException(40301): Not the session owner.
            AppException(40901): Session is not in_progress.
        """
        session = await self._get_session_or_404(session_id)
        self._check_ownership(session, user_id)

        if session.status != "in_progress":
            raise AppException(
                code=40901,
                message="操作与当前状态冲突",
                status_code=409,
            )

        # Get current max sequence
        max_seq = await self._get_max_sequence(session_id)
        candidate_seq = max_seq + 1

        # Insert candidate message
        answer = InterviewMessage(
            session_id=session_id,
            role="candidate",
            content=content,
            sequence=candidate_seq,
        )
        self._db.add(answer)
        await self._db.flush()

        # Check if max questions reached
        if session.question_count >= session.max_questions:
            await self._db.flush()
            return answer, None, True, session.question_count

        # Generate next question
        job_role = await self._load_job_role(session.job_role_id)
        messages = await self._load_messages(session_id)

        question_text, is_finished = await self._openai.generate_next_question(
            job_role_name=job_role.name_zh,
            difficulty=session.difficulty,
            max_questions=session.max_questions,
            question_count=session.question_count,
            messages=messages,
        )

        if is_finished:
            await self._db.flush()
            return answer, None, True, session.question_count

        # Insert interviewer message with new question
        interviewer_seq = candidate_seq + 1
        next_question = InterviewMessage(
            session_id=session_id,
            role="interviewer",
            content=question_text,
            sequence=interviewer_seq,
        )
        self._db.add(next_question)

        # Increment question_count
        new_count = session.question_count + 1
        await self._db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(question_count=new_count, updated_at=datetime.now(UTC))
        )
        await self._db.flush()

        return answer, next_question, False, new_count

    # -------------------------------------------------------------------------
    # Complete session — in_progress → completed
    # -------------------------------------------------------------------------

    async def complete_session(
        self, session_id: UUID, user_id: UUID
    ) -> InterviewSession:
        """Complete the interview and trigger report generation.

        Raises:
            AppException(40903): Not in_progress.
            AppException(40901): question_count == 0 (should cancel instead).
        """
        session = await self._get_session_or_404(session_id)
        self._check_ownership(session, user_id)

        if session.status != "in_progress":
            raise AppException(
                code=40903,
                message="面试会话状态不允许此操作",
                status_code=409,
            )

        if session.question_count < 1:
            raise AppException(
                code=40901,
                message="操作与当前状态冲突",
                status_code=409,
            )

        now = datetime.now(UTC)
        await self._db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(
                status="completed",
                ended_at=now,
                report_status="generating",
                updated_at=now,
            )
        )
        await self._db.flush()

        # Fire-and-forget: schedule report generation as a background task.
        # The task creates its own AsyncSession, so it will see the committed
        # data after the request's get_db dependency commits.
        ReportService.trigger_report_generation(session_id)

        return await self._load_session_with_relations(session_id)

    # -------------------------------------------------------------------------
    # Cancel session — pending/in_progress → cancelled
    # -------------------------------------------------------------------------

    async def cancel_session(
        self, session_id: UUID, user_id: UUID
    ) -> InterviewSession:
        """Cancel the interview.

        - pending → cancelled (always allowed)
        - in_progress → cancelled (only if question_count == 0)

        Raises:
            AppException(40903): Status not in pending/in_progress.
            AppException(40901): in_progress with questions (should complete).
        """
        session = await self._get_session_or_404(session_id)
        self._check_ownership(session, user_id)

        if session.status not in ("pending", "in_progress"):
            raise AppException(
                code=40903,
                message="面试会话状态不允许此操作",
                status_code=409,
            )

        if session.status == "in_progress" and session.question_count > 0:
            raise AppException(
                code=40901,
                message="操作与当前状态冲突",
                status_code=409,
            )

        now = datetime.now(UTC)
        await self._db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(
                status="cancelled",
                ended_at=now,
                updated_at=now,
            )
        )
        await self._db.flush()

        return await self._load_session_with_relations(session_id)

    # -------------------------------------------------------------------------
    # List / Detail queries
    # -------------------------------------------------------------------------

    async def list_sessions(
        self,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> tuple[list[dict], int]:
        """Return paginated session list items for the given user.

        Returns:
            (list_of_item_dicts, total_count)
        """
        query = select(InterviewSession).where(
            InterviewSession.user_id == user_id
        )
        count_query = select(func.count()).select_from(InterviewSession).where(
            InterviewSession.user_id == user_id
        )

        if status is not None:
            query = query.where(InterviewSession.status == status)
            count_query = count_query.where(InterviewSession.status == status)

        # Get total count
        total_result = await self._db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated items
        offset = (page - 1) * page_size
        query = (
            query.options(selectinload(InterviewSession.job_role))
            .order_by(InterviewSession.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self._db.execute(query)
        sessions = result.scalars().all()

        items = []
        for s in sessions:
            # Get overall_score from report if available
            overall_score = None
            if s.report_status == "ready":
                from app.models.interview_report import InterviewReport

                report_result = await self._db.execute(
                    select(InterviewReport.overall_score).where(
                        InterviewReport.session_id == s.id
                    )
                )
                score = report_result.scalar_one_or_none()
                if score is not None:
                    overall_score = float(score)

            items.append({
                "id": s.id,
                "jobRoleName": s.job_role.name_zh if s.job_role else None,
                "difficulty": s.difficulty,
                "mode": s.mode,
                "status": s.status,
                "questionCount": s.question_count,
                "reportStatus": s.report_status,
                "overallScore": overall_score,
                "createdAt": s.created_at,
            })

        return items, total

    async def get_session_detail(
        self, session_id: UUID, user_id: UUID
    ) -> InterviewSession:
        """Get session detail with messages.

        Raises:
            AppException(40403): Session not found.
            AppException(40301): Not the session owner.
        """
        session = await self._get_session_or_404(session_id)
        self._check_ownership(session, user_id)
        return await self._load_session_with_relations(session_id)

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_session_or_404(self, session_id: UUID) -> InterviewSession:
        """Load a session by ID or raise 40403."""
        result = await self._db.execute(
            select(InterviewSession).where(InterviewSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if session is None:
            raise AppException(
                code=40403, message="面试会话不存在", status_code=404
            )
        return session

    def _check_ownership(self, session: InterviewSession, user_id: UUID) -> None:
        """Verify session belongs to user, raise 40301 if not."""
        if session.user_id != user_id:
            raise AppException(
                code=40301, message="无权访问该资源", status_code=403
            )

    async def _load_session_with_relations(
        self, session_id: UUID
    ) -> InterviewSession:
        """Load session with job_role and messages eagerly."""
        result = await self._db.execute(
            select(InterviewSession)
            .where(InterviewSession.id == session_id)
            .options(
                selectinload(InterviewSession.job_role),
                selectinload(InterviewSession.messages),
            )
        )
        session = result.scalar_one()
        return session

    async def _load_job_role(self, job_role_id: UUID) -> JobRole:
        """Load a job role by ID."""
        result = await self._db.execute(
            select(JobRole).where(JobRole.id == job_role_id)
        )
        return result.scalar_one()

    async def _get_max_sequence(self, session_id: UUID) -> int:
        """Get the maximum sequence number for a session's messages."""
        result = await self._db.execute(
            select(func.max(InterviewMessage.sequence)).where(
                InterviewMessage.session_id == session_id
            )
        )
        max_seq = result.scalar_one_or_none()
        return max_seq or 0

    async def _load_messages(self, session_id: UUID) -> list[InterviewMessage]:
        """Load all messages for a session ordered by sequence."""
        result = await self._db.execute(
            select(InterviewMessage)
            .where(InterviewMessage.session_id == session_id)
            .order_by(InterviewMessage.sequence)
        )
        return list(result.scalars().all())
