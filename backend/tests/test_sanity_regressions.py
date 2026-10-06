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
from app.contracts.enums import NotificationDeliveryKind, NotificationDeliveryStatus
from app.contracts.errors import ConfigurationError
from app.models.notification_delivery import NotificationDelivery
from app.schemas.followup_item import FollowUpItemCreate
from app.services.notification_delivery_service import notification_delivery_service


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
