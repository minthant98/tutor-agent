"""add stripe and exam fields

Revision ID: b4e8f1a2c3d9
Revises: 97a43b5cd374
Create Date: 2026-05-30 00:00:00.000000

Adds to students:
  - exam_date            (Date, nullable)
  - subscription_status  (String(20), default 'active')
  - stripe_customer_id   (String(255), nullable)
  - stripe_subscription_id (String(255), nullable)
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b4e8f1a2c3d9'
down_revision: Union[str, Sequence[str], None] = '97a43b5cd374'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('exam_date', sa.Date(), nullable=True))
    op.add_column('students', sa.Column(
        'subscription_status',
        sa.String(length=20),
        nullable=False,
        server_default='active',
    ))
    op.add_column('students', sa.Column('stripe_customer_id', sa.String(length=255), nullable=True))
    op.add_column('students', sa.Column('stripe_subscription_id', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'stripe_subscription_id')
    op.drop_column('students', 'stripe_customer_id')
    op.drop_column('students', 'subscription_status')
    op.drop_column('students', 'exam_date')
