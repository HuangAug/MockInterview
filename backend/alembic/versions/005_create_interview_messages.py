"""Create interview_messages table.

Revision ID: 005
Revises: 004
Create Date: 2026-06-12

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "interview_messages",
        sa.Column("id", sa.Uuid(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("session_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("audio_url", sa.String(length=500), nullable=True),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "role IN ('interviewer', 'candidate')",
            name="chk_messages_role",
        ),
        sa.CheckConstraint(
            "sequence > 0",
            name="chk_messages_sequence",
        ),
        sa.UniqueConstraint(
            "session_id", "sequence", name="uq_messages_session_sequence"
        ),
        sa.ForeignKeyConstraint(
            ["session_id"],
            ["interview_sessions.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_messages_session_sequence",
        "interview_messages",
        ["session_id", "sequence"],
    )


def downgrade() -> None:
    op.drop_index("idx_messages_session_sequence", table_name="interview_messages")
    op.drop_table("interview_messages")
