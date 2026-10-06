"""next action and outcome reasons

Revision ID: 0004_next_action
Revises: 0003_pay_split
Create Date: 2026-04-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0004_next_action"
down_revision = "0003_pay_split"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("followup_items", sa.Column("next_action", sa.Text(), nullable=True))
    op.add_column("followup_items", sa.Column("done_reason", sa.Text(), nullable=True))
    op.add_column("followup_items", sa.Column("lost_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("followup_items", "lost_reason")
    op.drop_column("followup_items", "done_reason")
    op.drop_column("followup_items", "next_action")
