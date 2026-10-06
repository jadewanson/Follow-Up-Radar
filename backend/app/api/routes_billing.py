from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.billing import BillingCancelRequest, BillingSummaryResponse
from app.services.billing_service import billing_service

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/summary", response_model=BillingSummaryResponse)
def billing_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BillingSummaryResponse:
    return billing_service.get_summary(db, user=current_user)


@router.post("/start-trial", response_model=BillingSummaryResponse, status_code=status.HTTP_201_CREATED)
def start_trial(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BillingSummaryResponse:
    billing_service.start_trial(db, user=current_user)
    return billing_service.get_summary(db, user=current_user)


@router.post("/upgrade", response_model=BillingSummaryResponse)
def upgrade_to_pro(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> BillingSummaryResponse:
    billing_service.upgrade(db, user=current_user)
    return billing_service.get_summary(db, user=current_user)


@router.post("/cancel", response_model=BillingSummaryResponse)
def cancel_plan(
    payload: BillingCancelRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillingSummaryResponse:
    billing_service.cancel(db, user=current_user, reason=payload.reason)
    return billing_service.get_summary(db, user=current_user)
