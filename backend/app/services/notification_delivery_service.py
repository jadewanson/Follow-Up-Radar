from __future__ import annotations

import json
import smtplib
import ssl
import uuid
from dataclasses import dataclass
from email.message import EmailMessage as MimeEmailMessage
from email.utils import make_msgid
from pathlib import Path
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import (
    EmailDeliveryMode,
    NotificationDeliveryKind,
    NotificationDeliveryStatus,
    SmtpSecurity,
)
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


class EmailGateway(Protocol):
    def send(self, message: EmailMessage) -> str: ...


class FileEmailGateway:
    def __init__(self, outbox_path: str, from_address: str) -> None:
        if not outbox_path.strip():
            raise ConfigurationError("DEV_EMAIL_OUTBOX_PATH must not be empty")
        if not from_address.strip():
            raise ConfigurationError("EMAIL_FROM_ADDRESS must not be empty")
        self.outbox_path = Path(outbox_path)
        self.from_address = from_address
        self.outbox_path.parent.mkdir(parents=True, exist_ok=True)

    def send(self, message: EmailMessage) -> str:
        provider_message_id = str(uuid.uuid4())
        payload = {
            "provider_message_id": provider_message_id,
            "kind": message.kind.value,
            "idempotency_key": message.idempotency_key,
            "from_email": self.from_address,
            "to_email": message.to_email,
            "subject": message.subject,
            "body_text": message.body_text,
            "related_entity_type": message.related_entity_type,
            "related_entity_id": message.related_entity_id,
        }
        with self.outbox_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return provider_message_id


class SmtpEmailGateway:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        username: str | None,
        password: str | None,
        security: SmtpSecurity,
        timeout_seconds: int,
        from_address: str,
    ) -> None:
        if not host.strip():
            raise ConfigurationError("SMTP_HOST must not be empty")
        if not from_address.strip():
            raise ConfigurationError("EMAIL_FROM_ADDRESS must not be empty")
        if (username is None) != (password is None):
            raise ConfigurationError("SMTP_USERNAME and SMTP_PASSWORD must be configured together")
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.security = security
        self.timeout_seconds = timeout_seconds
        self.from_address = from_address

    def _login_if_configured(self, client: smtplib.SMTP) -> None:
        if self.username is not None and self.password is not None:
            client.login(self.username, self.password)

    def _send_with_client(self, client: smtplib.SMTP, message: MimeEmailMessage) -> None:
        refused = client.send_message(message)
        if refused:
            raise RuntimeError(f"SMTP server refused recipient(s): {', '.join(sorted(refused))}")

    def send(self, message: EmailMessage) -> str:
        mime_message = MimeEmailMessage()
        mime_message["From"] = self.from_address
        mime_message["To"] = message.to_email
        mime_message["Subject"] = message.subject
        mime_message["Message-ID"] = make_msgid()
        mime_message["X-Follow-Up-Radar-Idempotency-Key"] = message.idempotency_key
        mime_message.set_content(message.body_text)

        tls_context = ssl.create_default_context()
        if self.security == SmtpSecurity.SSL:
            with smtplib.SMTP_SSL(
                self.host,
                self.port,
                timeout=self.timeout_seconds,
                context=tls_context,
            ) as client:
                self._login_if_configured(client)
                self._send_with_client(client, mime_message)
        else:
            with smtplib.SMTP(
                self.host,
                self.port,
                timeout=self.timeout_seconds,
            ) as client:
                client.ehlo()
                if self.security == SmtpSecurity.STARTTLS:
                    client.starttls(context=tls_context)
                    client.ehlo()
                self._login_if_configured(client)
                self._send_with_client(client, mime_message)

        return str(mime_message["Message-ID"]).strip("<>")


class NotificationDeliveryService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.gateway: EmailGateway = self._build_gateway()

    def _build_gateway(self) -> EmailGateway:
        if self.settings.email_delivery_mode == EmailDeliveryMode.DEV_FILE:
            return FileEmailGateway(
                self.settings.dev_email_outbox_path,
                self.settings.email_from_address,
            )
        if self.settings.email_delivery_mode == EmailDeliveryMode.SMTP:
            if self.settings.smtp_host is None:
                raise ConfigurationError("SMTP_HOST is required for smtp delivery")
            return SmtpEmailGateway(
                host=self.settings.smtp_host,
                port=self.settings.smtp_port,
                username=self.settings.smtp_username,
                password=self.settings.smtp_password,
                security=self.settings.smtp_security,
                timeout_seconds=self.settings.smtp_timeout_seconds,
                from_address=self.settings.email_from_address,
            )
        raise ConfigurationError("Unsupported email delivery mode")

    def prepare(
        self,
        db: Session,
        *,
        message: EmailMessage,
        provider_name: str,
        persisted_body_text: str | None = None,
    ) -> NotificationDelivery:
        existing = db.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.idempotency_key == message.idempotency_key
            )
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
            body_text=persisted_body_text if persisted_body_text is not None else message.body_text,
            provider=provider_name,
            status=NotificationDeliveryStatus.PENDING.value,
        )
        db.add(delivery)
        db.flush()
        return delivery

    def _dispatch_message(
        self,
        *,
        delivery: NotificationDelivery,
        message: EmailMessage,
    ) -> bool:
        if delivery.status == NotificationDeliveryStatus.SENT.value:
            return True
        if delivery.status not in {
            NotificationDeliveryStatus.PENDING.value,
            NotificationDeliveryStatus.FAILED.value,
        }:
            return False

        now = utcnow()
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
        delivery.error_text = None
        delivery.sent_at = now
        delivery.updated_at = now
        return True

    def dispatch_message(
        self,
        *,
        delivery: NotificationDelivery,
        message: EmailMessage,
    ) -> bool:
        if message.idempotency_key != delivery.idempotency_key:
            raise ValidationError("Message idempotency key does not match delivery")
        if message.to_email != delivery.to_email:
            raise ValidationError("Message recipient does not match delivery")
        return self._dispatch_message(delivery=delivery, message=message)

    def dispatch_delivery(self, *, delivery: NotificationDelivery) -> bool:
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
        return self._dispatch_message(delivery=delivery, message=message)

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
