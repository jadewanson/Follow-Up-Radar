"""beta interest requests

Revision ID: 0005_beta_interest
Revises: 0004_next_action
Create Date: 2026-04-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_beta_interest"
down_revision = "0004_next_action"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "beta_interest_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_beta_interest_requests_user_id", "beta_interest_requests", ["user_id"])
    op.create_index("ix_beta_interest_requests_email", "beta_interest_requests", ["email"])


def downgrade() -> None:
    op.drop_index("ix_beta_interest_requests_email", table_name="beta_interest_requests")
    op.drop_index("ix_beta_interest_requests_user_id", table_name="beta_interest_requests")
    op.drop_table("beta_interest_requests")
