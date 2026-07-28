"""unique_progress_narrations

Revision ID: 20260727_unique_progress_narrations
Revises: 20260727_add_progress_narrations
Create Date: 2026-07-27

Follow-up to 20260727_add_progress_narrations.

Adds a UNIQUE constraint on (student_id, subject, computed_date) so that
pg_insert(...).on_conflict_do_update() can reference it by name and concurrent
cron runs cannot produce duplicate rows.

The existing composite index is kept for query performance; the unique constraint
provides the additional duplicate-prevention guarantee needed for the ON CONFLICT
upsert path.
"""
from alembic import op

revision = "20260727_uniq_prog_narrations"
down_revision = "20260727_add_progress_narrations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_progress_narrations_student_subject_date",
        "progress_narrations",
        ["student_id", "subject", "computed_date"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_progress_narrations_student_subject_date",
        "progress_narrations",
        type_="unique",
    )
