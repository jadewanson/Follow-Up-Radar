from __future__ import annotations

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
from app.models.reminder import Reminder
from app.services.auth_service import auth_service


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TEST_OUTBOX_FILE.unlink(missing_ok=True)


def _consume_magic_token(email: str) -> str:
    with SessionLocal() as db:
        row = db.execute(select(MagicLinkToken).where(MagicLinkToken.email == email)).scalar_one()
        raw = (email.replace("@", "_").replace(".", "_") + "_TOKEN_" * 8)[:48]
        row.token_hash = auth_service._hash_token(raw)  # noqa: SLF001
        db.commit()
        return raw


def _login(client: TestClient, email: str) -> str:
    req = client.post("/auth/request-magic-link", json={"email": email})
    assert req.status_code == 202, req.text
    token = _consume_magic_token(email)
    verify = client.post("/auth/verify", json={"email": email, "token": token})
    assert verify.status_code == 200, verify.text
    return verify.json()["access_token"]


def _create_item(client: TestClient, token: str, *, title: str, due_at: datetime):
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "client_name": "Client Signals",
            "type": "invoice",
            "due_at": due_at.isoformat(),
            "amount": "100.00",
            "currency": "usd",
        },
    )
    assert create.status_code == 201, create.text
    return create.json()


def test_registry_and_detail_surface_review_signals() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "signals@example.com")

    now = datetime.now(timezone.utc)
    paid_open = _create_item(client, token, title="Paid open", due_at=now + timedelta(days=2))
    stale_case = _create_item(client, token, title="Stale case", due_at=now + timedelta(days=2))
    reminder_failed = _create_item(client, token, title="Reminder failed", due_at=now - timedelta(days=1))

    paid_resp = client.post(f"/items/{paid_open['id']}/mark-paid", headers={"Authorization": f"Bearer {token}"})
    assert paid_resp.status_code == 200, paid_resp.text

    stale_item_id = UUID(stale_case["id"])
    failed_item_id = UUID(reminder_failed["id"])
    old_timestamp = now - timedelta(days=8)

    with SessionLocal() as db:
        from app.models.followup_item import FollowUpItem

        stale_followup = db.get(FollowUpItem, stale_item_id)
        stale_followup.created_at = old_timestamp
        stale_followup.updated_at = old_timestamp

        all_events = db.execute(select(EventLog)).scalars().all()
        for event in all_events:
            payload = event.payload_json or {}
            if event.entity_id == str(stale_item_id) or payload.get("item_id") == str(stale_item_id):
                event.created_at = old_timestamp

        failed_reminder = db.execute(select(Reminder).where(Reminder.item_id == failed_item_id)).scalar_one()
        failed_reminder.status = "failed"
        failed_reminder.last_error = "smtp timeout"
        db.commit()

    registry = client.get("/items/registry?scope=all", headers={"Authorization": f"Bearer {token}"})
    assert registry.status_code == 200, registry.text
    rows = {row["title"]: row for row in registry.json()["items"]}
    paid_codes = {signal["code"] for signal in rows["Paid open"]["review_signals"]}
    stale_codes = {signal["code"] for signal in rows["Stale case"]["review_signals"]}
    failed_codes = {signal["code"] for signal in rows["Reminder failed"]["review_signals"]}
    assert "paid_but_open" in paid_codes
    assert "stale_case" in stale_codes
    assert "reminder_failed" in failed_codes
    assert "overdue_without_reminder" in failed_codes

    filtered = client.get(
        "/items/registry?scope=all&review_signal=paid_but_open",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filtered.status_code == 200, filtered.text
    assert [row["title"] for row in filtered.json()["items"]] == ["Paid open"]

    detail = client.get(f"/items/{failed_item_id}", headers={"Authorization": f"Bearer {token}"})
    assert detail.status_code == 200, detail.text
    detail_codes = {signal["code"] for signal in detail.json()["review_signals"]}
    assert "reminder_failed" in detail_codes
    assert detail.json()["last_reminder_status"] == "failed"
    assert detail.json()["last_reminder_error"] == "smtp timeout"
