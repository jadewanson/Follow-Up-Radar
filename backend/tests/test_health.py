from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ["APP_ENV"] = "test"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["APP_BASE_URL"] = "http://localhost:5173"
os.environ["DATABASE_URL"] = f"sqlite:///{Path(tempfile.gettempdir()) / 'followup_radar_test.sqlite3'}"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["EMAIL_DELIVERY_MODE"] = "dev_file"
os.environ["EMAIL_FROM_ADDRESS"] = "noreply@followupradar.local"
os.environ["DEV_EMAIL_OUTBOX_PATH"] = str(Path(tempfile.gettempdir()) / 'followup_radar_test_outbox.jsonl')
os.environ["CORS_ALLOWED_ORIGINS"] = "http://localhost:5173"

from fastapi.testclient import TestClient

from app.main import app


def test_live_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
