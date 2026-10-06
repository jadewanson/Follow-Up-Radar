from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import (
    EventType,
    ItemStatus,
    NotificationDeliveryKind,
    ReminderStatus,
    TERMINAL_ITEM_STATUSES,
)
from app.models.followup_item import FollowUpItem
from app.models.reminder import Reminder
from app.models.user import User
from app.services.event_service import event_service
from app.services.item_service import item_service
from app.services.notification_delivery_service import EmailMessage, notification_delivery_service
from app.utils.datetime import coerce_utc, utcnow


class ReminderDispatchService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _render_reminder(self, *, user: User, item: FollowUpItem, reminder: Reminder) -> EmailMessage:
        due_at = coerce_utc(item.due_at).strftime("%Y-%m-%d %H:%M UTC")
        detail_url = f"{self.settings.app_base_url.rstrip('/')}/#/item/{item.id}"
        body = (
            f"Reminder for {item.client_name}\n\n"
            f"Title: {item.title}\n"
            f"Type: {item.type}\n"
            f"Due at: {due_at}\n"
            f"Current status: {item.status}\n"
            f"Open item: {detail_url}\n"
        )
        return EmailMessage(
            kind=NotificationDeliveryKind.REMINDER_EMAIL,
            idempotency_key=f"reminder:{reminder.id}",
            to_email=user.email,
            subject=f"Follow-Up Radar: {item.client_name} — {item.title}",
            body_text=body,
            related_entity_type="reminder",
            related_entity_id=str(reminder.id),
            user_id=user.id,
        )

    def dispatch_due(self, db: Session, *, limit: int = 100) -> int:
        item_service.reconcile_temporal_statuses(db)
        now = utcnow()
        rows = db.execute(
            select(Reminder, FollowUpItem, User)
            .join(FollowUpItem, FollowUpItem.id == Reminder.item_id)
            .join(User, User.id == Reminder.user_id)
            .where(
                Reminder.reminder_at <= now,
                Reminder.canceled_at.is_(None),
                Reminder.status.in_([ReminderStatus.PENDING.value, ReminderStatus.FAILED.value]),
            )
            .order_by(Reminder.reminder_at.asc(), Reminder.created_at.asc())
            .limit(limit)
        ).all()

        sent = 0
        for reminder, item, user in rows:
            item_status = ItemStatus(item.status)
            if item_status in TERMINAL_ITEM_STATUSES:
                reminder.status = ReminderStatus.CANCELED.value
                reminder.canceled_at = now
                continue
            if reminder.attempt_count >= self.settings.reminder_max_attempts:
                reminder.status = ReminderStatus.FAILED.value
                reminder.last_attempt_at = now
                reminder.last_error = "maximum delivery attempts exhausted"
                continue

            message = self._render_reminder(user=user, item=item, reminder=reminder)
            notification_delivery_service.ensure_message_shape(
                to_email=message.to_email,
                subject=message.subject,
                body_text=message.body_text,
            )
            delivery = notification_delivery_service.prepare(
                db,
                message=message,
                provider_name=self.settings.email_delivery_mode.value,
            )
            dispatched = notification_delivery_service.dispatch_delivery(delivery=delivery)
            reminder.attempt_count += 1
            reminder.last_attempt_at = utcnow()
            if dispatched and delivery.status == "sent":
                reminder.status = ReminderStatus.SENT.value
                reminder.sent_at = delivery.sent_at
                reminder.last_error = None
                event_service.record(
                    db,
                    event_type=EventType.REMINDER_SENT,
                    entity_type="reminder",
                    user_id=user.id,
                    entity_id=str(reminder.id),
                    payload={"item_id": str(item.id), "delivery_id": str(delivery.id)},
                )
                sent += 1
            else:
                reminder.status = ReminderStatus.FAILED.value
                reminder.last_error = delivery.error_text or "delivery dispatch failed"
                event_service.record(
                    db,
                    event_type=EventType.REMINDER_DISPATCH_FAILED,
                    entity_type="reminder",
                    user_id=user.id,
                    entity_id=str(reminder.id),
                    payload={"item_id": str(item.id), "delivery_id": str(delivery.id)},
                )
            db.commit()
        return sent


reminder_dispatch_service = ReminderDispatchService()
