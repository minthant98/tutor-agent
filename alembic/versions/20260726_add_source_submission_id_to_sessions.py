"""add_source_submission_id_to_sessions

Revision ID: 20260726_source_submission_id
Revises: 20260714_add_state_to_sessions
Create Date: 2026-07-26

Adds sessions.source_submission_id (nullable UUID) for Marker→Practice bridge
analytics. When a TutorSession is started from a GradedUpload result, this field
stores the submission's id so the loop-close event marker_recommended_practice_completed
can include the source context.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "20260726_source_submission_id"
down_revision = "b9c8d7e6f5a4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sessions",
        sa.Column(
            "source_submission_id",
            UUID(as_uuid=True),
            nullable=True,
            comment="Marker bridge: id of the GradedUpload that triggered this practice session",
        ),
    )


def downgrade() -> None:
    op.drop_column("sessions", "source_submission_id")
