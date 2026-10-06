"""lifecycle/payment split and paid-state correction

Revision ID: 0003_pay_split
Revises: 0002_dispatch_digest
Create Date: 2026-04-20
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_pay_split"
down_revision = "0002_dispatch_digest"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "followup_items",
        sa.Column("payment_status", sa.String(length=32), nullable=False, server_default="unpaid"),
    )
    op.create_index("ix_followup_items_payment_status", "followup_items", ["payment_status"], unique=False)

    op.execute(
        """
        UPDATE followup_items
        SET payment_status = CASE
            WHEN type IN ('proposal', 'lead', 'promised_reply') THEN 'not_applicable'
            ELSE 'unpaid'
        END
        """
    )
    op.execute(
        """
        UPDATE followup_items
        SET payment_status = 'paid', status = 'open', completed_at = NULL
        WHERE status = 'paid'
        """
    )
    op.alter_column("followup_items", "payment_status", server_default=None)

    op.execute(
        """
        UPDATE event_logs
        SET event_type = 'item_payment_status_changed',
            payload_json = (
                ((payload_json::jsonb - 'status') || jsonb_build_object('payment_status', 'paid'))::json
            )
        WHERE event_type = 'item_status_changed'
          AND payload_json->>'status' = 'paid'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE event_logs
        SET event_type = 'item_status_changed',
            payload_json = (payload_json - 'payment_status') || jsonb_build_object('status', 'paid')
        WHERE event_type = 'item_payment_status_changed'
          AND payload_json->>'payment_status' = 'paid'
        """
    )
    op.execute(
        """
        UPDATE followup_items
        SET status = 'paid', completed_at = COALESCE(completed_at, updated_at)
        WHERE payment_status = 'paid' AND status = 'open'
        """
    )
    op.drop_index("ix_followup_items_payment_status", table_name="followup_items")
    op.drop_column("followup_items", "payment_status")
