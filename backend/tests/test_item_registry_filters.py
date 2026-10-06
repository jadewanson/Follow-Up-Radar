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


def _create_item(client: TestClient, token: str, *, title: str, due_at: datetime, amount: str, item_type: str = "invoice"):
    create = client.post(
        "/items",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": title,
            "client_name": "Client Registry",
            "type": item_type,
            "due_at": due_at.isoformat(),
            "amount": amount,
            "currency": "usd",
            "next_action": f"Action for {title}",
        },
    )
    assert create.status_code == 201, create.text
    return create.json()


def test_registry_supports_search_sort_and_filters() -> None:
    _reset_db()
    client = TestClient(app)
    token = _login(client, "filters@example.com")

    now = datetime.now(timezone.utc)
    _create_item(client, token, title="Alpha invoice", due_at=now + timedelta(days=3), amount="50.00")
    bravo = _create_item(client, token, title="Bravo invoice", due_at=now + timedelta(days=1), amount="150.00")
    _create_item(client, token, title="Charlie invoice", due_at=now - timedelta(days=1), amount="300.00")
    _create_item(client, token, title="Delta lead", due_at=now + timedelta(days=2), amount="10.00", item_type="lead")

    paid = client.post(f"/items/{bravo['id']}/mark-paid", headers={"Authorization": f"Bearer {token}"})
    assert paid.status_code == 200, paid.text

    resp = client.get(
        "/items/registry?scope=all&q=invoice&sort_by=amount&sort_dir=desc&payment_status=unpaid",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    assert payload["counts"] == {"all": 2, "active": 2, "closed": 0}
    assert [row["title"] for row in payload["items"]] == ["Charlie invoice", "Alpha invoice"]

    overdue = client.get(
        "/items/registry?scope=active&due_bucket=overdue",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert overdue.status_code == 200, overdue.text
    assert [row["title"] for row in overdue.json()["items"]] == ["Charlie invoice"]

    due_range = client.get(
        f"/items/registry?scope=all&due_from={(now + timedelta(days=1)).date().isoformat()}&due_to={(now + timedelta(days=3)).date().isoformat()}&sort_by=due_at&sort_dir=asc",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert due_range.status_code == 200, due_range.text
    assert [row["title"] for row in due_range.json()["items"]] == ["Bravo invoice", "Delta lead", "Alpha invoice"]

    lead_only = client.get(
        "/items/registry?scope=all&item_type=lead",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert lead_only.status_code == 200, lead_only.text
    assert [row["title"] for row in lead_only.json()["items"]] == ["Delta lead"]
