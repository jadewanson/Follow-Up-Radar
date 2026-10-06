from __future__ import annotations

from datetime import datetime

from app.contracts.enums import ItemStatus, TERMINAL_ITEM_STATUSES
from app.contracts.errors import StateTransitionError
from app.utils.datetime import coerce_utc, utcnow

ALLOWED_TERMINAL_OUTCOMES = {ItemStatus.DONE, ItemStatus.LOST}


def reconcile_temporal_status(current_status: ItemStatus, due_at: datetime, now: datetime | None = None) -> ItemStatus:
    if current_status in TERMINAL_ITEM_STATUSES:
        return current_status

    reference_due_at = coerce_utc(due_at)
    reference_now = coerce_utc(now) if now is not None else utcnow()
    due_date = reference_due_at.date()
    now_date = reference_now.date()

    if due_date < now_date:
        return ItemStatus.OVERDUE
    if due_date == now_date:
        return ItemStatus.DUE_TODAY
    return ItemStatus.OPEN


def ensure_terminal_transition(current_status: ItemStatus, target_status: ItemStatus) -> None:
    if target_status not in ALLOWED_TERMINAL_OUTCOMES:
        raise StateTransitionError(f"Target terminal status {target_status.value} is not allowed")
    if current_status in TERMINAL_ITEM_STATUSES:
        raise StateTransitionError(
            f"Cannot transition terminal item from {current_status.value} to {target_status.value}"
        )


def ensure_mutable_status(current_status: ItemStatus) -> None:
    if current_status in TERMINAL_ITEM_STATUSES:
        raise StateTransitionError(f"Item in status {current_status.value} is immutable")


def ensure_archivable(current_status: ItemStatus) -> None:
    if current_status == ItemStatus.ARCHIVED:
        raise StateTransitionError("Item is already archived")
