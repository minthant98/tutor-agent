"""add_observations

Revision ID: a1b2c3d4e5f6
Revises: f1a2b3c4d5e6
Create Date: 2026-07-13

Additive migration for Task 8: Alex observations with traceability.
- Creates observations table with JSONB trace_json and composite index on
  (student_id, subject, week_of) for fast weekly look-ups.
- No changes to existing tables. No DROPs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "a1b2c3d4e5f6"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "observations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column(
            "student_id",
            UUID(as_uuid=True),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("subject", sa.String(64), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("trace_json", JSONB, nullable=False),
        sa.Column("week_of", sa.Date, nullable=False, index=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "idx_observations_student_subject_week",
        "observations",
        ["student_id", "subject", "week_of"],
    )


def downgrade():
    op.drop_index("idx_observations_student_subject_week", table_name="observations")
    op.drop_table("observations")
