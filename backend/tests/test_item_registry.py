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


def _create_item(client: TestClient, token: str, *, title: str, item_type: str = "invoice"):
    due_at = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "client_name": "Client Registry",
            "type": item_type,
            "due_at": due_at,
            "amount": "111.00",
            "currency": "usd",
            "note": "Registry smoke",
        },
    )
    assert create.status_code == 201, create.text
    return create.json()


def test_registry_returns_scoped_case_list_with_lifecycle_summary() -> None:
    _reset_db()
    client = TestClient(app)

    owner_token = _login(client, "owner-registry@example.com")
    other_token = _login(client, "other-registry@example.com")

    active_item = _create_item(client, owner_token, title="Active unpaid case")
    paid_item = _create_item(client, owner_token, title="Active paid case")
    paid_resp = client.post(f"/items/{paid_item['id']}/mark-paid", headers={"Authorization": f"Bearer {owner_token}"})
    assert paid_resp.status_code == 200, paid_resp.text

    closed_item = _create_item(client, owner_token, title="Closed case")
    complete = client.post(
        f"/items/{closed_item['id']}/complete",
        headers={"Authorization": f"Bearer {owner_token}"},
        json={"outcome": "done", "reason": "Paid and delivered"},
    )
    assert complete.status_code == 200, complete.text

    _create_item(client, other_token, title="Other case")

    all_cases = client.get("/items/registry?scope=all", headers={"Authorization": f"Bearer {owner_token}"})
    assert all_cases.status_code == 200, all_cases.text
    all_payload = all_cases.json()
    assert all_payload["scope"] == "all"
    assert {row["title"] for row in all_payload["items"]} == {"Active unpaid case", "Active paid case", "Closed case"}
    paid_row = next(row for row in all_payload["items"] if row["title"] == "Active paid case")
    assert paid_row["status"] == "open"
    assert paid_row["payment_status"] == "paid"
    assert paid_row["last_event_summary"] == "Payment status changed to paid"
    assert paid_row["last_event_at"] is not None

    active_cases = client.get("/items/registry?scope=active", headers={"Authorization": f"Bearer {owner_token}"})
    assert active_cases.status_code == 200, active_cases.text
    assert {row["title"] for row in active_cases.json()["items"]} == {"Active unpaid case", "Active paid case"}

    closed_cases = client.get("/items/registry?scope=closed", headers={"Authorization": f"Bearer {owner_token}"})
    assert closed_cases.status_code == 200, closed_cases.text
    assert [row["title"] for row in closed_cases.json()["items"]] == ["Closed case"]

    invalid = client.get("/items/registry?scope=weird", headers={"Authorization": f"Bearer {owner_token}"})
    assert invalid.status_code == 422, invalid.text

    other_view = client.get("/items/registry?scope=all", headers={"Authorization": f"Bearer {other_token}"})
    assert other_view.status_code == 200, other_view.text
    assert [row["title"] for row in other_view.json()["items"]] == ["Other case"]
