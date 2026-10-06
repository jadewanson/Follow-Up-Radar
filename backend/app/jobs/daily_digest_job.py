from __future__ import annotations

from app.db.session import SessionLocal
from app.services.daily_digest_service import daily_digest_service


def main() -> None:
    with SessionLocal() as db:
        sent = daily_digest_service.run_for_current_day(db)
    print(f"daily_digest_sent={sent}")


if __name__ == "__main__":
    main()
