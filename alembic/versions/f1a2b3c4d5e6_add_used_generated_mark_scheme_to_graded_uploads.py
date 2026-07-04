"""add_used_generated_mark_scheme_to_graded_uploads

Revision ID: f1a2b3c4d5e6
Revises: aeaa5034fcb2
Create Date: 2026-07-04

Additive migration — adds used_generated_mark_scheme boolean column to
graded_uploads. Existing rows receive server_default=false so the column is
immediately non-nullable with no back-fill step required.
"""
from alembic import op
import sqlalchemy as sa

revision = "f1a2b3c4d5e6"
down_revision = "aeaa5034fcb2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "graded_uploads",
        sa.Column(
            "used_generated_mark_scheme",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade():
    op.drop_column("graded_uploads", "used_generated_mark_scheme")
