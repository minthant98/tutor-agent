"""add_progress_narrations

Revision ID: 20260727_add_progress_narrations
Revises: 20260726_marker_analytics_cols
Create Date: 2026-07-27

Additive migration for Task 31: nightly LLM progress narration cache.
- Creates progress_narrations table keyed by (student_id, subject, computed_date).
- Composite index for fast cache-hit look-ups.
- No changes to existing tables. No DROPs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

revision = "20260727_add_progress_narrations"
down_revision = "20260726_marker_analytics_cols"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "progress_narrations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "student_id",
            UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(64), nullable=False, index=True),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("computed_date", sa.Date, nullable=False, index=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_progress_narrations_student_subject_date",
        "progress_narrations",
        ["student_id", "subject", "computed_date"],
    )


def downgrade() -> None:
    op.drop_index(
        "idx_progress_narrations_student_subject_date",
        table_name="progress_narrations",
    )
    op.drop_table("progress_narrations")
