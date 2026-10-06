from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

TEST_DB_FILE = Path(tempfile.gettempdir()) / "followup_radar_test.sqlite3"
TEST_OUTBOX_FILE = Path(tempfile.gettempdir()) / "followup_radar_test_outbox.jsonl"
os.environ["APP_ENV"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["APP_BASE_URL"] = "http://localhost:5173"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["EMAIL_DELIVERY_MODE"] = "dev_file"
os.environ["EMAIL_FROM_ADDRESS"] = "noreply@followupradar.local"
os.environ["DEV_EMAIL_OUTBOX_PATH"] = str(TEST_OUTBOX_FILE)
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.auth_token import MagicLinkToken
from app.models.event_log import EventLog
from app.models.notification_delivery import NotificationDelivery
from app.models.reminder import Reminder
from app.services.daily_digest_service import daily_digest_service
from app.services.reminder_dispatch_service import reminder_dispatch_service


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TEST_OUTBOX_FILE.unlink(missing_ok=True)


def _consume_magic_token(email: str) -> str:
    with SessionLocal() as db:
        row = db.execute(select(MagicLinkToken).where(MagicLinkToken.email == email)).scalar_one()
        raw = "T" * 48
        from app.services.auth_service import auth_service

        row.token_hash = auth_service._hash_token(raw)  # noqa: SLF001 - deliberate test seam
        db.commit()
        return raw


def test_auth_item_reminder_event_flow() -> None:
    _reset_db()
    client = TestClient(app)

    email = "user@example.com"
    resp = client.post("/auth/request-magic-link", json={"email": email})
    assert resp.status_code == 202, resp.text
    assert TEST_OUTBOX_FILE.exists()
    outbox_lines = TEST_OUTBOX_FILE.read_text(encoding="utf-8").strip().splitlines()
    assert len(outbox_lines) == 1
    delivery_payload = json.loads(outbox_lines[0])
    assert delivery_payload["kind"] == "magic_link_email"
    assert delivery_payload["from_email"] == "noreply@followupradar.local"
    assert delivery_payload["to_email"] == email
    assert "#/verify?" in delivery_payload["body_text"]

    with SessionLocal() as db:
        magic_delivery = db.execute(
            select(NotificationDelivery).where(
                NotificationDelivery.kind == "magic_link_email"
            )
        ).scalar_one()
        assert "#/verify?" not in magic_delivery.body_text
        assert "token=" not in magic_delivery.body_text
        assert "one-time authentication secret" in magic_delivery.body_text

    raw_token = _consume_magic_token(email)
    verify = client.post("/auth/verify", json={"email": email, "token": raw_token})
    assert verify.status_code == 200, verify.text
    access_token = verify.json()["access_token"]

    due_at = (datetime.now(timezone.utc) - timedelta(days=1, hours=1)).isoformat()
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "title": "Follow up invoice 1024",
            "client_name": "Client A",
            "type": "invoice",
            "due_at": due_at,
            "amount": "250.00",
            "currency": "usd",
            "note": "Sent yesterday",
        },
    )
    assert create.status_code == 201, create.text
    item_id = create.json()["id"]
    assert create.json()["payment_status"] == "unpaid"

    board = client.get("/items/board", headers={"Authorization": f"Bearer {access_token}"})
    assert board.status_code == 200, board.text
    assert len(board.json()["overdue"]) == 1

    with SessionLocal() as db:
        reminder = db.execute(
            select(Reminder).where(Reminder.item_id == UUID(item_id))
        ).scalar_one_or_none()
        assert reminder is not None
        events = db.execute(select(EventLog)).scalars().all()
        event_types = {event.event_type for event in events}
        assert "item_created" in event_types
        assert "reminder_created" in event_types

        reminder_sent = reminder_dispatch_service.dispatch_due(db)
        assert reminder_sent == 1

        reminder = db.execute(select(Reminder).where(Reminder.id == reminder.id)).scalar_one()
        assert reminder.status == "sent"
        deliveries = db.execute(select(NotificationDelivery)).scalars().all()
        kinds = {delivery.kind for delivery in deliveries}
        assert "magic_link_email" in kinds
        assert "reminder_email" in kinds

        digest_sent = daily_digest_service.run_for_current_day(db)
        assert digest_sent == 1
        digest_sent_repeat = daily_digest_service.run_for_current_day(db)
        assert digest_sent_repeat == 0

    mark_paid = client.post(
        f"/items/{item_id}/mark-paid",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert mark_paid.status_code == 200, mark_paid.text
    assert mark_paid.json()["status"] == "overdue"
    assert mark_paid.json()["payment_status"] == "paid"

    complete = client.post(
        f"/items/{item_id}/complete",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"outcome": "done", "reason": "Paid and delivered"},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "done"
    assert complete.json()["payment_status"] == "paid"
