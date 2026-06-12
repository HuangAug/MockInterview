"""Create interview_reports table.

Revision ID: 006
Revises: 005
Create Date: 2026-06-12

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_reports",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("overall_score", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column(
            "communication_score", sa.Numeric(precision=5, scale=2), nullable=False
        ),
        sa.Column(
            "technical_score", sa.Numeric(precision=5, scale=2), nullable=False
        ),
        sa.Column(
            "problem_solving_score", sa.Numeric(precision=5, scale=2), nullable=False
        ),
        sa.Column(
            "structure_score", sa.Numeric(precision=5, scale=2), nullable=False
        ),
        sa.Column("strengths", postgresql.JSONB(), nullable=False),
        sa.Column("weaknesses", postgresql.JSONB(), nullable=False),
        sa.Column("suggestions", postgresql.JSONB(), nullable=False),
        sa.Column("question_feedback", postgresql.JSONB(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("session_id", name="uq_reports_session_id"),
        sa.CheckConstraint(
            "overall_score >= 0 AND overall_score <= 100",
            name="chk_reports_overall_score",
        ),
        sa.CheckConstraint(
            "communication_score >= 0 AND communication_score <= 100",
            name="chk_reports_communication_score",
        ),
        sa.CheckConstraint(
            "technical_score >= 0 AND technical_score <= 100",
            name="chk_reports_technical_score",
        ),
        sa.CheckConstraint(
            "problem_solving_score >= 0 AND problem_solving_score <= 100",
            name="chk_reports_problem_solving_score",
        ),
        sa.CheckConstraint(
            "structure_score >= 0 AND structure_score <= 100",
            name="chk_reports_structure_score",
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["interview_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_reports_session_id", "interview_reports", ["session_id"])


def downgrade() -> None:
    op.drop_index("idx_reports_session_id", table_name="interview_reports")
    op.drop_table("interview_reports")
