"""add_state_to_sessions

Revision ID: b9c8d7e6f5a4
Revises: a1b2c3d4e5f6
Create Date: 2026-07-14

Task 14: Autosave — adds nullable JSONB `state` column to sessions table.
Existing rows get NULL (treated as empty dict in the endpoint).
No DROPs, no table recreations.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "b9c8d7e6f5a4"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "sessions",
        sa.Column("state", JSONB, nullable=True),
    )


def downgrade():
    op.drop_column("sessions", "state")
