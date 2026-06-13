"""ReportService — async report generation via background task."""

import asyncio
import logging
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppException
from app.db.session import async_session_factory
from app.models.interview_message import InterviewMessage
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
from app.models.job_role import JobRole
from app.services.openai_service import OpenAIService

logger = logging.getLogger(__name__)


class ReportService:
    """Handles async report generation as a background task."""

    @staticmethod
    def trigger_report_generation(session_id: UUID) -> None:
        """Fire-and-forget: schedule report generation as a background task.

        Called from the complete endpoint. Does not block the HTTP response.
        The task creates its own AsyncSession (independent of the request session).
        """
        asyncio.create_task(ReportService._generate_report_task(session_id))

    @staticmethod
    async def _generate_report_task(session_id: UUID) -> None:
        """Background task: generate report via OpenAI and persist to DB.

        Uses an independent AsyncSession to avoid SessionClosed errors
        after the HTTP request completes.
        """
        try:
            async with async_session_factory() as db:
                # Load session
                session_result = await db.execute(
                    select(InterviewSession)
                    .where(InterviewSession.id == session_id)
                )
                session = session_result.scalar_one_or_none()
                if session is None:
                    logger.error(
                        "Report task: session %s not found", session_id
                    )
                    return

                # Load job role
                job_role_result = await db.execute(
                    select(JobRole).where(JobRole.id == session.job_role_id)
                )
                job_role = job_role_result.scalar_one_or_none()
                if job_role is None:
                    logger.error(
                        "Report task: job role %s not found",
                        session.job_role_id,
                    )
                    await ReportService._set_status(db, session_id, "failed")
                    return

                # Load messages
                messages_result = await db.execute(
                    select(InterviewMessage)
                    .where(InterviewMessage.session_id == session_id)
                    .order_by(InterviewMessage.sequence)
                )
                messages: list[InterviewMessage] = list(
                    messages_result.scalars().all()
                )

                # Generate report via OpenAI
                openai_svc = OpenAIService()
                report_data = await openai_svc.generate_report(
                    job_role_name=job_role.name_zh,
                    difficulty=session.difficulty,
                    question_count=session.question_count,
                    messages=messages,
                )

                # Write report to interview_reports table
                report = InterviewReport(
                    session_id=session_id,
                    overall_score=Decimal(str(report_data["overallScore"])),
                    communication_score=Decimal(
                        str(report_data["communicationScore"])
                    ),
                    technical_score=Decimal(
                        str(report_data["technicalScore"])
                    ),
                    problem_solving_score=Decimal(
                        str(report_data["problemSolvingScore"])
                    ),
                    structure_score=Decimal(
                        str(report_data["structureScore"])
                    ),
                    strengths=report_data["strengths"],
                    weaknesses=report_data["weaknesses"],
                    suggestions=report_data["suggestions"],
                    question_feedback=report_data["questionFeedback"],
                    summary=report_data["summary"],
                )
                db.add(report)

                # Update report_status to ready
                await ReportService._set_status(db, session_id, "ready")
                await db.commit()
                logger.info(
                    "Report generated successfully for session %s",
                    session_id,
                )

        except AppException:
            # OpenAI or validation failure
            await ReportService._safe_set_status(session_id, "failed")
            logger.error(
                "Report generation failed for session %s",
                session_id,
                exc_info=True,
            )
        except Exception:
            # Unexpected error
            await ReportService._safe_set_status(session_id, "failed")
            logger.error(
                "Report generation crashed for session %s",
                session_id,
                exc_info=True,
            )

    @staticmethod
    async def _set_status(
        db: AsyncSession, session_id: UUID, status: str
    ) -> None:
        """Update report_status on the session within an existing db session."""
        from datetime import UTC, datetime

        await db.execute(
            update(InterviewSession)
            .where(InterviewSession.id == session_id)
            .values(report_status=status, updated_at=datetime.now(UTC))
        )
        await db.flush()

    @staticmethod
    async def _safe_set_status(session_id: UUID, status: str) -> None:
        """Update report_status using a fresh session (for error recovery)."""
        try:
            async with async_session_factory() as db:
                await ReportService._set_status(db, session_id, status)
                await db.commit()
        except Exception:
            logger.error(
                "Failed to update report_status to %s for session %s",
                status,
                session_id,
                exc_info=True,
            )
