from __future__ import annotations

from app.db.session import SessionLocal
from app.services.reminder_dispatch_service import reminder_dispatch_service


def main() -> None:
    with SessionLocal() as db:
        sent = reminder_dispatch_service.dispatch_due(db)
    print(f"reminder_dispatch_sent={sent}")


if __name__ == "__main__":
    main()
