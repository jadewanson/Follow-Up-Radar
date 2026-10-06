from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.enums import EventType
from app.models.event_log import EventLog
from app.models.followup_item import FollowUpItem


def _coerce_optional_uuid(value: uuid.UUID | str | None) -> uuid.UUID | None:
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    return uuid.UUID(str(value))


class EventService:
    def record(self, db: Session, *, event_type: EventType, entity_type: str, user_id: uuid.UUID | str | None, entity_id: str | None, payload: dict[str, Any] | None = None) -> EventLog:
        event = EventLog(
            user_id=_coerce_optional_uuid(user_id),
            event_type=event_type.value,
            entity_type=entity_type,
            entity_id=entity_id,
            payload_json=payload or {},
        )
        db.add(event)
        return event

    def summarize(self, event: EventLog | None) -> str | None:
        if event is None:
            return None
        payload = event.payload_json or {}
        if event.event_type == EventType.ITEM_CREATED.value:
            return "Case created"
        if event.event_type == EventType.ITEM_UPDATED.value:
            return "Case updated"
        if event.event_type == EventType.ITEM_ARCHIVED.value:
            return "Case archived"
        if event.event_type == EventType.ITEM_REOPENED.value:
            return f"Case reopened as {payload.get('status')}" if payload.get('status') else 'Case reopened'
        if event.event_type == EventType.ITEM_RESCHEDULED.value:
            due_at = payload.get("due_at")
            return f"Due date rescheduled to {due_at}" if due_at else "Case rescheduled"
        if event.event_type == EventType.ITEM_STATUS_CHANGED.value:
            status = payload.get("status")
            reason = payload.get("reason")
            if status and reason:
                return f"Case status changed to {status} — {reason}"
            return f"Case status changed to {status}" if status else "Case status changed"
        if event.event_type == EventType.ITEM_PAYMENT_STATUS_CHANGED.value:
            payment_status = payload.get("payment_status")
            return f"Payment status changed to {payment_status}" if payment_status else "Payment status changed"
        if event.event_type == EventType.ITEM_NEXT_ACTION_UPDATED.value:
            next_action = payload.get("next_action")
            return f"Next action set to {next_action}" if next_action else "Next action cleared"
        if event.event_type == EventType.REMINDER_CREATED.value:
            reminder_at = payload.get("reminder_at")
            return f"Reminder scheduled for {reminder_at}" if reminder_at else "Reminder scheduled"
        if event.event_type == EventType.REMINDER_SENT.value:
            return "Reminder sent"
        if event.event_type == EventType.REMINDER_DISPATCH_FAILED.value:
            return "Reminder delivery failed"
        if event.event_type == EventType.BILLING_TRIAL_STARTED.value:
            return "Beta trial started"
        if event.event_type == EventType.BILLING_UPGRADED.value:
            return "Plan upgraded to Pro"
        if event.event_type == EventType.BILLING_CANCELED.value:
            return "Plan canceled"
        return event.event_type.replace("_", " ").capitalize()

    def list_for_item(self, db: Session, *, user_id: uuid.UUID | str, item: FollowUpItem) -> list[EventLog]:
        events = db.execute(
            select(EventLog).where(EventLog.user_id == _coerce_optional_uuid(user_id)).order_by(EventLog.created_at.desc())
        ).scalars().all()

        item_id = str(item.id)
        filtered: list[EventLog] = []
        for event in events:
            payload = event.payload_json or {}
            if event.entity_type == "followup_item" and event.entity_id == item_id:
                filtered.append(event)
                continue
            if payload.get("item_id") == item_id:
                filtered.append(event)
        return filtered

    def latest_for_items(self, db: Session, *, user_id: uuid.UUID | str, items: list[FollowUpItem]) -> dict[str, EventLog]:
        item_ids = {str(item.id) for item in items}
        if not item_ids:
            return {}

        events = db.execute(
            select(EventLog).where(EventLog.user_id == _coerce_optional_uuid(user_id)).order_by(EventLog.created_at.desc())
        ).scalars().all()

        latest: dict[str, EventLog] = {}
        for event in events:
            payload = event.payload_json or {}
            item_id: str | None = None
            if event.entity_type == "followup_item" and event.entity_id in item_ids:
                item_id = event.entity_id
            elif payload.get("item_id") in item_ids:
                item_id = payload.get("item_id")
            if item_id is None or item_id in latest:
                continue
            latest[item_id] = event
            if len(latest) == len(item_ids):
                break
        return latest


event_service = EventService()
