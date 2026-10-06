from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import (
    AuthTokenResponse,
    CurrentUserResponse,
    RequestMagicLinkRequest,
    RequestMagicLinkResponse,
    VerifyMagicLinkRequest,
)
from app.services.auth_service import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/request-magic-link", response_model=RequestMagicLinkResponse, status_code=status.HTTP_202_ACCEPTED)
def request_magic_link(payload: RequestMagicLinkRequest, db: Session = Depends(get_db)) -> RequestMagicLinkResponse:
    auth_service.issue_magic_link(db, payload.email)
    return RequestMagicLinkResponse(status="accepted")


@router.post("/verify", response_model=AuthTokenResponse)
def verify_magic_link(payload: VerifyMagicLinkRequest, db: Session = Depends(get_db)) -> AuthTokenResponse:
    _, access_token, expires_at = auth_service.verify_magic_link(db, payload.email, payload.token)
    return AuthTokenResponse(access_token=access_token, expires_at=expires_at)


@router.get("/me", response_model=CurrentUserResponse)
def get_me(current_user: User = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=str(current_user.id),
        email=current_user.email,
        timezone=current_user.timezone,
        plan=current_user.plan,
        plan_status=current_user.plan_status,
        created_at=current_user.created_at,
    )
