"""ux_overhaul_v1

Revision ID: e80cc37a44f4
Revises: e3c1d92ab47f
Create Date: 2026-06-29 18:49:12.368894

Adds tables and columns for the UX overhaul sub-project #1:
- learner_subjects, syllabus_topics, readiness_snapshots, notifications, today_focus_history
- students.preferences, onboarded_at, is_admin
- sessions.session_type, session_version, segment_plan, current_segment_idx
Backfills learner_subjects from existing Student flat fields.
Seeds syllabus_topics for Pure Maths × Edexcel 9MA0 and Cambridge 9709 (version 2026.1).
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

from app.core.syllabus_seed import EDEXCEL_9MA0_TOPICS, CAMBRIDGE_9709_TOPICS, SYLLABUS_VERSION

# revision identifiers, used by Alembic.
revision = 'e80cc37a44f4'
down_revision = 'e3c1d92ab47f'
branch_labels = None
depends_on = None


def upgrade():
    # ---- learner_subjects ----
    op.create_table(
        "learner_subjects",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("exam_level", sa.String(20), nullable=False, server_default="a_level"),
        sa.Column("exam_date", sa.Date, nullable=True),
        sa.Column("target_grade", sa.String(2), nullable=False, server_default="A"),
        sa.Column("current_grade", sa.String(2), nullable=True),
        sa.Column("syllabus_version", sa.String(20), nullable=False, server_default=SYLLABUS_VERSION),
        sa.Column("recommended_minutes_per_day", sa.Integer, nullable=True),
        sa.Column("is_draft", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "subject", name="uq_learner_subjects_student_subject"),
    )

    # ---- syllabus_topics ----
    op.create_table(
        "syllabus_topics",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("exam_board", sa.String(50), nullable=False),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("version", sa.String(20), nullable=False),
        sa.Column("topic_id", sa.String(100), nullable=False),
        sa.Column("topic_name", sa.String(255), nullable=False),
        sa.Column("parent_topic_id", sa.String(100), nullable=True),
        sa.Column("ordinal", sa.Integer, nullable=False, server_default="0"),
        sa.UniqueConstraint("exam_board", "subject", "version", "topic_id",
                            name="uq_syllabus_board_subject_version_topic"),
    )

    # ---- readiness_snapshots ----
    op.create_table(
        "readiness_snapshots",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("snapshot_date", sa.Date, nullable=False),
        sa.Column("readiness_pct", sa.Float, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("student_id", "subject", "snapshot_date",
                            name="uq_readiness_student_subject_date"),
    )

    # ---- notifications ----
    op.create_table(
        "notifications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("payload", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_notifications_student_read_created",
                    "notifications", ["student_id", "read_at", sa.text("created_at DESC")])

    # ---- today_focus_history ----
    op.create_table(
        "today_focus_history",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("subject", sa.String(100), nullable=False),
        sa.Column("focus_date", sa.Date, nullable=False),
        sa.Column("generator_version", sa.String(20), nullable=False),
        sa.Column("shape", sa.String(50), nullable=False),
        sa.Column("segment_plan", JSONB, nullable=False),
        sa.Column("reasoning", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("student_id", "subject", "focus_date",
                            name="uq_today_focus_student_subject_date"),
    )

    # ---- students new columns ----
    op.add_column("students", sa.Column("preferences", JSONB, nullable=False, server_default=sa.text("'{}'::jsonb")))
    op.add_column("students", sa.Column("onboarded_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("students", sa.Column("is_admin", sa.Boolean, nullable=False, server_default=sa.text("false")))

    # ---- sessions new columns ----
    op.add_column("sessions", sa.Column("session_type", sa.String(20), nullable=False, server_default="practice"))
    op.add_column("sessions", sa.Column("session_version", sa.Integer, nullable=False, server_default="2"))
    op.add_column("sessions", sa.Column("segment_plan", JSONB, nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.add_column("sessions", sa.Column("current_segment_idx", sa.Integer, nullable=False, server_default="0"))

    # ---- backfill: legacy sessions -> v1 ----
    op.execute("UPDATE sessions SET session_version = 1 WHERE started_at < NOW()")

    # ---- backfill: learner_subjects from existing Student flat fields ----
    op.execute("""
        INSERT INTO learner_subjects
            (id, student_id, subject, exam_board, exam_level, exam_date,
             target_grade, syllabus_version, is_draft)
        SELECT
            gen_random_uuid(),
            s.id,
            jsonb_array_elements_text(
                CASE WHEN jsonb_typeof(to_jsonb(s.subjects)) = 'array'
                     THEN to_jsonb(s.subjects)
                     ELSE '[]'::jsonb END
            ) AS subject,
            COALESCE(s.exam_board, 'edexcel'),
            COALESCE(s.exam_level, 'a_level'),
            s.exam_date,
            'A',
            '2026.1',
            false  -- not drafts; existing students are real
        FROM students s
        WHERE s.onboarding_complete = true
          AND s.subjects IS NOT NULL
          AND jsonb_typeof(to_jsonb(s.subjects)) = 'array'
        ON CONFLICT (student_id, subject) DO NOTHING
    """)

    # ---- seed syllabus_topics ----
    syllabus_rows = []
    for t in EDEXCEL_9MA0_TOPICS:
        syllabus_rows.append({
            "id": uuid.uuid4(),
            "exam_board": "edexcel", "subject": "pure_mathematics",
            "version": SYLLABUS_VERSION, **t,
        })
    for t in CAMBRIDGE_9709_TOPICS:
        syllabus_rows.append({
            "id": uuid.uuid4(),
            "exam_board": "cambridge", "subject": "pure_mathematics",
            "version": SYLLABUS_VERSION, **t,
        })
    op.bulk_insert(
        sa.table("syllabus_topics",
                 sa.column("id", UUID(as_uuid=True)),
                 sa.column("exam_board", sa.String),
                 sa.column("subject", sa.String),
                 sa.column("version", sa.String),
                 sa.column("topic_id", sa.String),
                 sa.column("topic_name", sa.String),
                 sa.column("parent_topic_id", sa.String),
                 sa.column("ordinal", sa.Integer)),
        syllabus_rows,
    )


def downgrade():
    # Additive migration; downgrade drops only the new objects.
    op.drop_column("sessions", "current_segment_idx")
    op.drop_column("sessions", "segment_plan")
    op.drop_column("sessions", "session_version")
    op.drop_column("sessions", "session_type")
    op.drop_column("students", "is_admin")
    op.drop_column("students", "onboarded_at")
    op.drop_column("students", "preferences")
    op.drop_table("today_focus_history")
    op.drop_index("ix_notifications_student_read_created", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("readiness_snapshots")
    op.drop_table("syllabus_topics")
    op.drop_table("learner_subjects")
