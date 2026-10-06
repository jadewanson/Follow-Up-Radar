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
from app.models.subscription import Subscription


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


def test_activation_summary_and_sample_case_bootstrap() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "activation@example.com")

    summary = client.get("/v1/system/activation-summary", headers={"Authorization": f"Bearer {token}"})
    assert summary.status_code == 200, summary.text
    payload = summary.json()
    assert payload["total_cases"] == 0
    assert payload["should_show_activation"] is True

    sample = client.post("/v1/system/bootstrap-sample-case", headers={"Authorization": f"Bearer {token}"})
    assert sample.status_code == 201, sample.text
    sample_payload = sample.json()
    assert sample_payload["next_action"] == "Send a payment reminder tomorrow"

    refreshed = client.get("/v1/system/activation-summary", headers={"Authorization": f"Bearer {token}"})
    assert refreshed.status_code == 200, refreshed.text
    refreshed_payload = refreshed.json()
    assert refreshed_payload["total_cases"] == 1
    assert any(m["code"] == "first_case" and m["completed"] for m in refreshed_payload["milestones"])


def test_billing_trial_upgrade_and_cancel_flow() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "billing@example.com")

    summary = client.get("/billing/summary", headers={"Authorization": f"Bearer {token}"})
    assert summary.status_code == 200, summary.text
    assert summary.json()["plan"] == "free"
    assert summary.json()["can_start_trial"] is True

    trial = client.post("/billing/start-trial", headers={"Authorization": f"Bearer {token}"})
    assert trial.status_code == 201, trial.text
    trial_payload = trial.json()
    assert trial_payload["plan"] == "pro"
    assert trial_payload["plan_status"] == "trialing"
    assert trial_payload["trial_ends_at"] is not None

    upgrade = client.post("/billing/upgrade", headers={"Authorization": f"Bearer {token}"})
    assert upgrade.status_code == 200, upgrade.text
    upgrade_payload = upgrade.json()
    assert upgrade_payload["plan"] == "pro"
    assert upgrade_payload["plan_status"] == "active"

    missing_reason = client.post("/billing/cancel", headers={"Authorization": f"Bearer {token}"}, json={"reason": ""})
    assert missing_reason.status_code == 422, missing_reason.text

    cancel = client.post(
        "/billing/cancel",
        headers={"Authorization": f"Bearer {token}"},
        json={"reason": "Beta workflow finished"},
    )
    assert cancel.status_code == 200, cancel.text
    cancel_payload = cancel.json()
    assert cancel_payload["plan"] == "free"
    assert cancel_payload["plan_status"] == "active"

    with SessionLocal() as db:
        subscription = db.execute(select(Subscription)).scalar_one()
        assert subscription.status == "canceled"
        assert subscription.cancel_reason == "Beta workflow finished"
