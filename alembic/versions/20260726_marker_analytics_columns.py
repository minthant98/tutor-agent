"""marker_analytics_columns

Revision ID: 20260726_marker_analytics_cols
Revises: 20260726_source_submission_id
Create Date: 2026-07-26

Adds two nullable columns for Marker v3 analytics:
- graded_uploads.time_to_submit_seconds (Float, nullable) — client-measured seconds from
  question shown to submission; used for marker_time_to_submit_seconds event.
"""
from alembic import op
import sqlalchemy as sa

revision = "20260726_marker_analytics_cols"
down_revision = "20260726_source_submission_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "graded_uploads",
        sa.Column(
            "time_to_submit_seconds",
            sa.Float(),
            nullable=True,
            comment="Client-measured seconds from question shown to submission",
        ),
    )


def downgrade() -> None:
    op.drop_column("graded_uploads", "time_to_submit_seconds")
