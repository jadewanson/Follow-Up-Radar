from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import EmailDeliveryMode, NotificationDeliveryKind, NotificationDeliveryStatus
from app.contracts.errors import ConfigurationError, ValidationError
from app.models.notification_delivery import NotificationDelivery
from app.utils.datetime import utcnow


@dataclass(frozen=True)
class EmailMessage:
    kind: NotificationDeliveryKind
    idempotency_key: str
    to_email: str
    subject: str
    body_text: str
    related_entity_type: str | None
    related_entity_id: str | None
    user_id: uuid.UUID | None


class FileEmailGateway:
    def __init__(self, outbox_path: str) -> None:
        if not outbox_path.strip():
            raise ConfigurationError("DEV_EMAIL_OUTBOX_PATH must not be empty")
        self.outbox_path = Path(outbox_path)
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, message: EmailMessage) -> str:
        provider_message_id = str(uuid.uuid4())
        payload = {
            "provider_message_id": provider_message_id,
            "kind": message.kind.value,
            "idempotency_key": message.idempotency_key,
            "to_email": message.to_email,
            "subject": message.subject,
            "body_text": message.body_text,
            "related_entity_type": message.related_entity_type,
            "related_entity_id": message.related_entity_id,
        }
        with self.outbox_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return provider_message_id


class NotificationDeliveryService:
    def __init__(self) -> None:
        self.settings = get_settings()
        if self.settings.email_delivery_mode == EmailDeliveryMode.DEV_FILE:
            self.gateway = FileEmailGateway(self.settings.dev_email_outbox_path)
        else:
            raise ConfigurationError("Unsupported email delivery mode")

    def prepare(
        self,
        db: Session,
        *,
        message: EmailMessage,
        provider_name: str,
    ) -> NotificationDelivery:
        existing = db.execute(
            select(NotificationDelivery).where(NotificationDelivery.idempotency_key == message.idempotency_key)
        ).scalar_one_or_none()
        if existing is not None:
            return existing

        delivery = NotificationDelivery(
            user_id=message.user_id,
            kind=message.kind.value,
            idempotency_key=message.idempotency_key,
            related_entity_type=message.related_entity_type,
            related_entity_id=message.related_entity_id,
            to_email=message.to_email,
            subject=message.subject,
            body_text=message.body_text,
            provider=provider_name,
            status=NotificationDeliveryStatus.PENDING.value,
        )
        db.add(delivery)
        db.flush()
        return delivery

    def dispatch_delivery(self, *, delivery: NotificationDelivery) -> bool:
        if delivery.status != NotificationDeliveryStatus.PENDING.value:
            return delivery.status == NotificationDeliveryStatus.SENT.value
        now = utcnow()
        message = EmailMessage(
            kind=NotificationDeliveryKind(delivery.kind),
            idempotency_key=delivery.idempotency_key,
            to_email=delivery.to_email,
            subject=delivery.subject,
            body_text=delivery.body_text,
            related_entity_type=delivery.related_entity_type,
            related_entity_id=delivery.related_entity_id,
            user_id=delivery.user_id,
        )
        try:
            provider_message_id = self.gateway.send(message)
        except Exception as exc:
            delivery.attempt_count += 1
            delivery.status = NotificationDeliveryStatus.FAILED.value
            delivery.error_text = str(exc)
            delivery.updated_at = now
            return False

        delivery.attempt_count += 1
        delivery.provider_message_id = provider_message_id
        delivery.status = NotificationDeliveryStatus.SENT.value
        delivery.sent_at = now
        delivery.updated_at = now
        return True

    def dispatch_pending(self, db: Session, *, limit: int = 100) -> int:
        deliveries = db.execute(
            select(NotificationDelivery)
            .where(NotificationDelivery.status == NotificationDeliveryStatus.PENDING.value)
            .order_by(NotificationDelivery.created_at.asc())
            .limit(limit)
        ).scalars().all()
        sent = 0
        for delivery in deliveries:
            if self.dispatch_delivery(delivery=delivery):
                sent += 1
        return sent

    def ensure_message_shape(self, *, to_email: str, subject: str, body_text: str) -> None:
        if not to_email.strip():
            raise ValidationError("Notification to_email must not be empty")
        if not subject.strip():
            raise ValidationError("Notification subject must not be empty")
        if not body_text.strip():
            raise ValidationError("Notification body_text must not be empty")


notification_delivery_service = NotificationDeliveryService()
