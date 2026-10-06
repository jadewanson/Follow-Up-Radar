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
os.environ["SUPPORT_EMAIL_ADDRESS"] = "support@followup-radar.local"
os.environ["BETA_TRIAL_DAYS"] = "14"
os.environ["PRO_MONTHLY_PRICE_USD"] = "9"

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.main import app
from app.models.auth_token import MagicLinkToken
from app.models.beta_interest_request import BetaInterestRequest
from app.models.reminder import Reminder


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


def test_terminal_reasons_required_and_case_can_reopen() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "reopen@example.com")

    due_at = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Reopen me",
            "client_name": "Client Reopen",
            "type": "invoice",
            "due_at": due_at,
            "amount": "10.00",
            "currency": "usd",
            "next_action": "Send reminder",
        },
    )
    assert create.status_code == 201, create.text
    item_id = create.json()["id"]

    missing_reason = client.post(
        f"/items/{item_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"outcome": "done"},
    )
    assert missing_reason.status_code == 422, missing_reason.text

    done = client.post(
        f"/items/{item_id}/complete",
        headers={"Authorization": f"Bearer {token}"},
        json={"outcome": "done", "reason": "Delivered successfully"},
    )
    assert done.status_code == 200, done.text
    assert done.json()["status"] == "done"
    assert done.json()["done_reason"] == "Delivered successfully"

    reopen = client.post(f"/items/{item_id}/reopen", headers={"Authorization": f"Bearer {token}"})
    assert reopen.status_code == 200, reopen.text
    assert reopen.json()["status"] == "open"
    assert reopen.json()["next_action"] is None

    with SessionLocal() as db:
        reminders = db.execute(
            select(Reminder).where(Reminder.item_id == item_id).order_by(Reminder.created_at.asc())
        ).scalars().all()
        assert [reminder.status for reminder in reminders] == ["canceled", "pending"]

    events = client.get(f"/items/{item_id}/events", headers={"Authorization": f"Bearer {token}"})
    assert events.status_code == 200, events.text
    event_types = [row["event_type"] for row in events.json()]
    assert "item_reopened" in event_types


def test_public_site_config_and_beta_interest_capture() -> None:
    _reset_db()
    client = TestClient(app)

    config = client.get("/v1/system/public-site-config")
    assert config.status_code == 200, config.text
    payload = config.json()
    assert payload["pro_monthly_price_usd"] == 9
    assert payload["beta_trial_days"] == 14
    assert payload["support_email"] == "support@followup-radar.local"

    interest = client.post(
        "/v1/system/beta-interest",
        json={"email": "beta@example.com", "note": "Need invoice workflow", "source": "pricing_page"},
    )
    assert interest.status_code == 202, interest.text
    assert interest.json()["status"] == "accepted"

    with SessionLocal() as db:
        stored = db.execute(select(BetaInterestRequest)).scalar_one()
        assert stored.email == "beta@example.com"
        assert stored.source == "pricing_page"
