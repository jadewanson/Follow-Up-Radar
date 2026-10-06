from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from redis import Redis
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db.session import SessionLocal
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.followup_item import FollowUpItemRead
from app.schemas.system import (
    ActivationSummaryResponse,
    BetaInterestRequestCreate,
    BetaInterestResponse,
    PublicSiteConfigResponse,
)
from app.services.activation_service import activation_service
from app.services.beta_interest_service import beta_interest_service
from app.services.item_service import item_service

health_router = APIRouter(tags=["health"])
system_router = APIRouter()


@health_router.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}


@health_router.get("/health/ready")
def ready() -> dict[str, str]:
    settings = get_settings()
    try:
        with SessionLocal() as session:
            session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"reason": "database_not_ready", "error": str(exc)},
        ) from exc

    try:
        redis_client = Redis.from_url(settings.redis_url, decode_responses=True)
        if redis_client.ping() is not True:
            raise RuntimeError("redis ping did not return True")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"reason": "redis_not_ready", "error": str(exc)},
        ) from exc

    return {"status": "ready"}


@system_router.get("/version")
def version() -> dict[str, str]:
    return {
        "service": "follow-up-radar-backend",
        "version": "0.14.0-iter14",
        "build_id": "local-development",
    }


@system_router.get("/public-site-config", response_model=PublicSiteConfigResponse)
def public_site_config() -> PublicSiteConfigResponse:
    settings = get_settings()
    return PublicSiteConfigResponse(
        product_name="Follow-Up Radar",
        tagline="No client case goes invisible.",
        support_email=settings.support_email_address,
        beta_trial_days=settings.beta_trial_days,
        pro_monthly_price_usd=settings.pro_monthly_price_usd,
        free_plan_name="Free",
        pro_plan_name="Pro",
        beta_message="Start with a beta trial, then upgrade when Radar becomes part of your weekly review loop.",
    )


@system_router.post("/beta-interest", response_model=BetaInterestResponse, status_code=status.HTTP_202_ACCEPTED)
def beta_interest(payload: BetaInterestRequestCreate, db: Session = Depends(get_db)) -> BetaInterestResponse:
    request = beta_interest_service.create(
        db,
        email=payload.email,
        note=payload.note,
        source=payload.source,
    )
    return BetaInterestResponse(status="accepted", created_at=request.created_at)


@system_router.get("/activation-summary", response_model=ActivationSummaryResponse)
def activation_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivationSummaryResponse:
    return activation_service.summary_for_user(db, user=current_user)


@system_router.post("/bootstrap-sample-case", response_model=FollowUpItemRead, status_code=status.HTTP_201_CREATED)
def bootstrap_sample_case(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpItemRead:
    item = activation_service.bootstrap_sample_case(db, user=current_user)
    return item_service.get_read(db, user=current_user, item_id=item.id)
