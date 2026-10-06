from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.beta_interest_request import BetaInterestRequest
from app.utils.datetime import utcnow


class BetaInterestService:
    def create(
        self,
        db: Session,
        *,
        email: str,
        note: str | None = None,
        source: str = "pricing",
        user_id: uuid.UUID | None = None,
    ) -> BetaInterestRequest:
        request = BetaInterestRequest(
            user_id=user_id,
            email=email.strip().lower(),
            note=(note.strip() or None) if note else None,
            source=source.strip().lower() or "pricing",
            created_at=utcnow(),
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request


beta_interest_service = BetaInterestService()
