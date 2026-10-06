"""dispatch, digest and notification deliveries

Revision ID: 0002_dispatch_digest
Revises: 0001_baseline
Create Date: 2026-04-19
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_dispatch_digest"
down_revision = "0001_baseline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("reminders", sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reminders", sa.Column("last_error", sa.Text(), nullable=True))
    op.alter_column("reminders", "attempt_count", server_default=None)

    op.create_table(
        "notification_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("kind", sa.String(length=64), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("related_entity_type", sa.String(length=64), nullable=True),
        sa.Column("related_entity_id", sa.Text(), nullable=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=False),
        sa.Column("provider", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("provider_message_id", sa.String(length=255), nullable=True),
        sa.Column("error_text", sa.Text(), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("idempotency_key", name="uq_notification_deliveries_idempotency_key"),
    )
    op.create_index("ix_notification_deliveries_user_id", "notification_deliveries", ["user_id"], unique=False)
    op.create_index("ix_notification_deliveries_kind", "notification_deliveries", ["kind"], unique=False)
    op.create_index(
        "ix_notification_deliveries_idempotency_key",
        "notification_deliveries",
        ["idempotency_key"],
        unique=True,
    )
    op.create_index("ix_notification_deliveries_status", "notification_deliveries", ["status"], unique=False)
    op.alter_column("notification_deliveries", "attempt_count", server_default=None)


def downgrade() -> None:
    op.drop_index("ix_notification_deliveries_status", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_idempotency_key", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_kind", table_name="notification_deliveries")
    op.drop_index("ix_notification_deliveries_user_id", table_name="notification_deliveries")
    op.drop_table("notification_deliveries")
    op.drop_column("reminders", "last_error")
    op.drop_column("reminders", "last_attempt_at")
    op.drop_column("reminders", "attempt_count")
