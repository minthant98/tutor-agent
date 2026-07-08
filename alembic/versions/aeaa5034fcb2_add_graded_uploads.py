"""add_graded_uploads

Revision ID: aeaa5034fcb2
Revises: e80cc37a44f4
Create Date: 2026-07-04

Additive migration for sub-project #3 Exam Marker.
- Creates graded_uploads table + 2 indexes
- No changes to existing tables. No DROPs.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = "aeaa5034fcb2"
down_revision = "e80cc37a44f4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "graded_uploads",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True),
                  sa.ForeignKey("students.id", ondelete="CASCADE"),
                  nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("question_id", sa.String(255), nullable=False),
        sa.Column("question_text", sa.Text, nullable=False),
        sa.Column("mark_scheme", sa.Text, nullable=False),
        sa.Column("max_marks", sa.Integer, nullable=False),
        sa.Column("input_type", sa.String(20), nullable=False),
        sa.Column("photo_path", sa.String(500), nullable=True),
        sa.Column("answer_text", sa.Text, nullable=True),
        sa.Column("marks_awarded", sa.Integer, nullable=True),
        sa.Column("grade_pct", sa.Numeric, nullable=True),
        sa.Column("feedback_json", JSONB, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "idx_graded_uploads_student_created",
        "graded_uploads",
        ["student_id", sa.text("created_at DESC")],
    )
    op.create_index(
        "idx_graded_uploads_student_status",
        "graded_uploads",
        ["student_id", "status"],
    )


def downgrade():
    op.drop_index("idx_graded_uploads_student_status", table_name="graded_uploads")
    op.drop_index("idx_graded_uploads_student_created", table_name="graded_uploads")
    op.drop_table("graded_uploads")
