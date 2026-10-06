from __future__ import annotations

from typing import Generator

from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app.contracts.errors import AuthenticationError
from app.db.session import SessionLocal
from app.models.user import User
from app.services.auth_service import auth_service


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if authorization is None or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing Authorization: Bearer token")
    raw_token = authorization[len("Bearer ") :].strip()
    return auth_service.authenticate_bearer(db, raw_token)
