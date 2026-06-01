"""Add onboarding_complete flag to students

Revision ID: d8a2f4b9c1e6
Revises: c7f3e2d1a8b5
Create Date: 2026-06-01

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'd8a2f4b9c1e6'
down_revision: Union[str, Sequence[str], None] = 'c7f3e2d1a8b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Idempotent: column may already exist from manual prod patch
    op.execute("ALTER TABLE students ADD COLUMN IF NOT EXISTS onboarding_complete BOOLEAN NOT NULL DEFAULT FALSE")
    # Backfill: anyone who already has subjects must have completed onboarding
    op.execute("UPDATE students SET onboarding_complete = TRUE WHERE subjects::text NOT IN ('[]', 'null', '')")


def downgrade() -> None:
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS onboarding_complete")
