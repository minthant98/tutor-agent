"""add study_plans table

Revision ID: c7f3e2d1a8b5
Revises: b4e8f1a2c3d9
Create Date: 2026-05-31
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = 'c7f3e2d1a8b5'
down_revision: Union[str, Sequence[str], None] = 'b4e8f1a2c3d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'study_plans',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('subject', sa.String(100), nullable=False),
        sa.Column('weeks_remaining', sa.Integer(), nullable=False),
        sa.Column('plan', sa.JSON(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_study_plans_student_subject', 'study_plans', ['student_id', 'subject'])


def downgrade() -> None:
    op.drop_index('ix_study_plans_student_subject', table_name='study_plans')
    op.drop_table('study_plans')
