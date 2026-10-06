"""billing self-serve hardening

Revision ID: 0006_billing_selfserve
Revises: 0005_beta_interest
Create Date: 2026-04-21
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = "0006_billing_selfserve"
down_revision = "0005_beta_interest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("subscriptions", sa.Column("trial_ends_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("subscriptions", sa.Column("cancel_reason", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("subscriptions", "cancel_reason")
    op.drop_column("subscriptions", "trial_ends_at")
