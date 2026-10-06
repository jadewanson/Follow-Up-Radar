from __future__ import annotations

import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

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


def _reset_db() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    TEST_OUTBOX_FILE.unlink(missing_ok=True)


def _consume_magic_token(email: str) -> str:
    with SessionLocal() as db:
        row = db.execute(select(MagicLinkToken).where(MagicLinkToken.email == email)).scalar_one()
        raw = (email.replace("@", "_").replace(".", "_") + "_TOKEN_" * 8)[:48]
        from app.services.auth_service import auth_service

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


def test_next_action_and_outcome_reasons_persist_and_surface_in_events() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "next-action@example.com")

    due_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Need final delivery",
            "client_name": "Client X",
            "type": "invoice",
            "due_at": due_at,
            "amount": "99.00",
            "currency": "usd",
            "next_action": "Send final files",
        },
    )
    assert create.status_code == 201, create.text
    item_id = create.json()["id"]
    assert create.json()["next_action"] == "Send final files"

    update = client.patch(
        f"/items/{item_id}",
        headers={"Authorization": f"Bearer {token}"},
        json={"next_action": "Confirm receipt of files"},
    )
    assert update.status_code == 200, update.text
    assert update.json()["next_action"] == "Confirm receipt of files"

    complete = client.post(
        f"/items/{item_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"outcome": "done", "reason": "Paid and delivered"},
    )
    assert complete.status_code == 200, complete.text
    assert complete.json()["status"] == "done"
    assert complete.json()["done_reason"] == "Paid and delivered"
    assert complete.json()["next_action"] is None

    events = client.get(f"/items/{item_id}/events", headers={"Authorization": f"Bearer {token}"})
    assert events.status_code == 200, events.text
    payload = events.json()
    event_types = [row["event_type"] for row in payload]
    assert "item_next_action_updated" in event_types
    assert payload[0]["summary"] == "Case status changed to done — Paid and delivered"
    next_action_event = next(row for row in payload if row["event_type"] == "item_next_action_updated")
    assert next_action_event["summary"] == "Next action set to Confirm receipt of files"

    closed = client.get("/items/registry?scope=closed", headers={"Authorization": f"Bearer {token}"})
    assert closed.status_code == 200, closed.text
    assert closed.json()["items"][0]["done_reason"] == "Paid and delivered"
