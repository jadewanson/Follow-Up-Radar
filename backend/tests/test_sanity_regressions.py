from __future__ import annotations

import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticValidationError

TEST_OUTBOX_FILE = Path(tempfile.gettempdir()) / "followup_radar_sanity_outbox.jsonl"
os.environ["APP_ENV"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["APP_BASE_URL"] = "http://localhost:5173"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.gettempdir()) / 'followup_radar_sanity.sqlite3'}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["EMAIL_DELIVERY_MODE"] = "dev_file"
os.environ["EMAIL_FROM_ADDRESS"] = "noreply@followupradar.local"
os.environ["DEV_EMAIL_OUTBOX_PATH"] = str(TEST_OUTBOX_FILE)
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"

from app.config import _parse_int
from app.contracts.enums import (
    NotificationDeliveryKind,
    NotificationDeliveryStatus,
    SmtpSecurity,
)
from app.contracts.errors import ConfigurationError
from app.models.notification_delivery import NotificationDelivery
from app.schemas.followup_item import FollowUpItemCreate
from app.services.notification_delivery_service import (
    EmailMessage,
    SmtpEmailGateway,
    notification_delivery_service,
)


def test_digest_hour_accepts_midnight(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DAILY_DIGEST_HOUR_UTC", "0")
    assert _parse_int("DAILY_DIGEST_HOUR_UTC", default=7, minimum=0, maximum=23) == 0

    monkeypatch.setenv("DAILY_DIGEST_HOUR_UTC", "24")
    with pytest.raises(ConfigurationError):
        _parse_int("DAILY_DIGEST_HOUR_UTC", default=7, minimum=0, maximum=23)


def test_failed_notification_delivery_can_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    class SuccessGateway:
        def send(self, _message) -> str:
            return "provider-message-1"

    monkeypatch.setattr(notification_delivery_service, "gateway", SuccessGateway())
    delivery = NotificationDelivery(
        user_id=None,
        kind=NotificationDeliveryKind.DAILY_DIGEST_EMAIL.value,
        idempotency_key="test-retry",
        related_entity_type="daily_digest",
        related_entity_id="2026-10-07",
        to_email="user@example.com",
        subject="Digest",
        body_text="Body",
        provider="dev_file",
        status=NotificationDeliveryStatus.FAILED.value,
        attempt_count=1,
        error_text="temporary failure",
    )

    assert notification_delivery_service.dispatch_delivery(delivery=delivery) is True
    assert delivery.status == NotificationDeliveryStatus.SENT.value
    assert delivery.attempt_count == 2
    assert delivery.provider_message_id == "provider-message-1"
    assert delivery.error_text is None


def test_smtp_gateway_uses_starttls_auth_and_from_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clients: list[FakeSmtp] = []

    class FakeSmtp:
        def __init__(self, host: str, port: int, timeout: int) -> None:
            self.host = host
            self.port = port
            self.timeout = timeout
            self.ehlo_count = 0
            self.started_tls = False
            self.login_args: tuple[str, str] | None = None
            self.sent_message = None
            clients.append(self)

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            return None

        def ehlo(self) -> None:
            self.ehlo_count += 1

        def starttls(self, *, context) -> None:
            assert context is not None
            self.started_tls = True

        def login(self, username: str, password: str) -> None:
            self.login_args = (username, password)

        def send_message(self, message):
            self.sent_message = message
            return {}

    monkeypatch.setattr(
        "app.services.notification_delivery_service.smtplib.SMTP",
        FakeSmtp,
    )
    gateway = SmtpEmailGateway(
        host="smtp.example.com",
        port=587,
        username="smtp-user",
        password="smtp-password",
        security=SmtpSecurity.STARTTLS,
        timeout_seconds=10,
        from_address="radar@example.com",
    )
    message = EmailMessage(
        kind=NotificationDeliveryKind.REMINDER_EMAIL,
        idempotency_key="reminder:1",
        to_email="user@example.com",
        subject="Follow up",
        body_text="Reminder body",
        related_entity_type="reminder",
        related_entity_id="1",
        user_id=None,
    )

    provider_message_id = gateway.send(message)

    client = clients[0]
    assert client.host == "smtp.example.com"
    assert client.port == 587
    assert client.timeout == 10
    assert client.started_tls is True
    assert client.ehlo_count == 2
    assert client.login_args == ("smtp-user", "smtp-password")
    assert client.sent_message["From"] == "radar@example.com"
    assert client.sent_message["To"] == "user@example.com"
    assert client.sent_message["X-Follow-Up-Radar-Idempotency-Key"] == "reminder:1"
    assert provider_message_id


def test_source_url_rejects_non_http_schemes() -> None:
    with pytest.raises(PydanticValidationError):
        FollowUpItemCreate(
            title="Unsafe link",
            client_name="Client",
            type="invoice",
            source_url="javascript:alert(1)",
            due_at=datetime.now(timezone.utc),
        )

    payload = FollowUpItemCreate(
        title="Safe link",
        client_name="Client",
        type="invoice",
        source_url=" https://example.com/case/1 ",
        due_at=datetime.now(timezone.utc),
    )
    assert payload.source_url == "https://example.com/case/1"
