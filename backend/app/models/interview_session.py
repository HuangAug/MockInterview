"""InterviewSession ORM model — maps to the `interview_sessions` table."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.interview_message import InterviewMessage
    from app.models.interview_report import InterviewReport
    from app.models.job_role import JobRole
    from app.models.user import User


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default="gen_random_uuid()"
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    job_role_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("job_roles.id", ondelete="RESTRICT"), nullable=False
    )
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    mode: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    question_count: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )
    max_questions: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="8"
    )
    report_status: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="pending"
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Relationships
    user: Mapped[User] = relationship(
        back_populates="interview_sessions"
    )
    job_role: Mapped[JobRole] = relationship(
        back_populates="interview_sessions"
    )
    messages: Mapped[list[InterviewMessage]] = relationship(
        back_populates="session", order_by="InterviewMessage.sequence"
    )
    report: Mapped[InterviewReport | None] = relationship(
        back_populates="session", uselist=False
    )
