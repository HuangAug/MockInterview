"""JobRole ORM model — maps to the `job_roles` table."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.interview_session import InterviewSession
    from app.models.user import User


class JobRole(Base):
    __tablename__ = "job_roles"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, server_default="gen_random_uuid()"
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    name_zh: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="true"
    )

    # Relationships
    targeting_users: Mapped[list[User]] = relationship(
        back_populates="target_job_role"
    )
    interview_sessions: Mapped[list[InterviewSession]] = relationship(
        back_populates="job_role"
    )
