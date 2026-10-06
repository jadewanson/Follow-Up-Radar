from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.enums import EventType, ReminderStatus
from app.models.followup_item import FollowUpItem
from app.models.reminder import Reminder
from app.services.event_service import event_service
from app.utils.datetime import coerce_utc, utcnow


class ReminderService:
    def _coerce_uuid(self, value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def create_for_item(self, db: Session, *, item: FollowUpItem) -> Reminder:
        reminder = Reminder(
            item_id=item.id,
            user_id=item.user_id,
            reminder_at=item.due_at,
            status=ReminderStatus.PENDING.value,
        )
        db.add(reminder)
        db.flush()
        event_service.record(
            db,
            event_type=EventType.REMINDER_CREATED,
            entity_type="reminder",
            user_id=item.user_id,
            entity_id=str(reminder.id),
            payload={
                "item_id": str(item.id),
                "reminder_at": coerce_utc(item.due_at).isoformat(),
                "status": reminder.status,
            },
        )
        return reminder

    def update_pending_for_item(self, db: Session, *, item: FollowUpItem) -> None:
        reminder = db.execute(
            select(Reminder)
            .where(Reminder.item_id == item.id, Reminder.status == ReminderStatus.PENDING.value)
            .order_by(Reminder.created_at.desc())
        ).scalar_one_or_none()
        if reminder is not None:
            reminder.reminder_at = item.due_at
            return
        self.create_for_item(db, item=item)

    def cancel_pending_for_item(self, db: Session, *, item_id: uuid.UUID | str) -> None:
        reminders = db.execute(
            select(Reminder).where(
                Reminder.item_id == self._coerce_uuid(item_id),
                Reminder.status == ReminderStatus.PENDING.value,
            )
        ).scalars().all()
        now = utcnow()
        for reminder in reminders:
            reminder.status = ReminderStatus.CANCELED.value
            reminder.canceled_at = now


reminder_service = ReminderService()
