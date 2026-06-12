"""Create interview_sessions table.

Revision ID: 004
Revises: 003
Create Date: 2026-06-12

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_sessions",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("job_role_id", sa.Uuid(), nullable=False),
        sa.Column("difficulty", sa.String(length=20), nullable=False),
        sa.Column("mode", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column(
            "question_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "max_questions",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("8"),
        ),
        sa.Column(
            "report_status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'pending'"),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "difficulty IN ('junior', 'mid', 'senior')",
            name="chk_sessions_difficulty",
        ),
        sa.CheckConstraint(
            "mode IN ('text', 'voice')",
            name="chk_sessions_mode",
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'cancelled', 'failed')",
            name="chk_sessions_status",
        ),
        sa.CheckConstraint(
            "report_status IN ('pending', 'generating', 'ready', 'failed')",
            name="chk_sessions_report_status",
        ),
        sa.CheckConstraint(
            "question_count >= 0",
            name="chk_sessions_question_count",
        ),
        sa.CheckConstraint(
            "max_questions > 0",
            name="chk_sessions_max_questions",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["job_role_id"],
            ["job_roles.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_sessions_user_created",
        "interview_sessions",
        ["user_id", sa.text("created_at DESC")],
    )
    op.create_index("idx_sessions_status", "interview_sessions", ["status"])
    op.create_index(
        "idx_sessions_user_status", "interview_sessions", ["user_id", "status"]
    )


def downgrade() -> None:
    op.drop_index("idx_sessions_user_status", table_name="interview_sessions")
    op.drop_index("idx_sessions_status", table_name="interview_sessions")
    op.drop_index("idx_sessions_user_created", table_name="interview_sessions")
    op.drop_table("interview_sessions")
