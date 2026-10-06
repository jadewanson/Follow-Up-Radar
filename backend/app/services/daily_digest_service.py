from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import EventType, ItemStatus, NotificationDeliveryKind
from app.models.followup_item import FollowUpItem
from app.models.user import User
from app.services.event_service import event_service
from app.services.item_service import item_service
from app.services.notification_delivery_service import EmailMessage, notification_delivery_service
from app.utils.datetime import utcnow


class DailyDigestService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _digest_key(self, user_id: str, digest_for: date) -> str:
        return f"daily_digest:{user_id}:{digest_for.isoformat()}"

    def _render_digest(self, *, user: User, items: list[FollowUpItem], digest_for: date) -> EmailMessage:
        lines = [
            f"Daily digest for {digest_for.isoformat()}",
            "",
            "Items requiring attention:",
        ]
        sorted_items = sorted(items, key=lambda item: item.due_at)
        for item in sorted_items:
            lines.append(
                f"- [{item.status}] {item.client_name} — {item.title} — due {item.due_at.astimezone().strftime('%Y-%m-%d %H:%M %Z')}"
            )
        lines.append("")
        lines.append(f"Open dashboard: {self.settings.app_base_url.rstrip('/')}/#/")
        return EmailMessage(
            kind=NotificationDeliveryKind.DAILY_DIGEST_EMAIL,
            idempotency_key=self._digest_key(str(user.id), digest_for),
            to_email=user.email,
            subject=f"Follow-Up Radar daily digest — {digest_for.isoformat()}",
            body_text="\n".join(lines),
            related_entity_type="daily_digest",
            related_entity_id=digest_for.isoformat(),
            user_id=user.id,
        )

    def run_for_current_day(self, db: Session) -> int:
        item_service.reconcile_temporal_statuses(db)
        today = utcnow().date()
        rows = db.execute(
            select(FollowUpItem, User)
            .join(User, User.id == FollowUpItem.user_id)
            .where(FollowUpItem.status.in_([ItemStatus.DUE_TODAY.value, ItemStatus.OVERDUE.value]))
            .order_by(FollowUpItem.user_id.asc(), FollowUpItem.due_at.asc())
        ).all()
        grouped: dict[str, tuple[User, list[FollowUpItem]]] = {}
        for item, user in rows:
            bucket = grouped.setdefault(str(user.id), (user, []))
            bucket[1].append(item)

        sent = 0
        for user_key, (user, items) in grouped.items():
            message = self._render_digest(user=user, items=items, digest_for=today)
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
            if delivery.status == "sent":
                continue
            dispatched = notification_delivery_service.dispatch_delivery(delivery=delivery)
            if dispatched and delivery.status == "sent":
                event_service.record(
                    db,
                    event_type=EventType.DAILY_DIGEST_SENT,
                    entity_type="daily_digest",
                    user_id=user.id,
                    entity_id=user_key,
                    payload={"delivery_id": str(delivery.id), "item_count": len(items), "digest_for": today.isoformat()},
                )
                sent += 1
            db.commit()
        return sent


daily_digest_service = DailyDigestService()
