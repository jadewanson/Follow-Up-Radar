from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from app.contracts.enums import Plan, PlanStatus


class BillingSummaryResponse(BaseModel):
    plan: Plan
    plan_status: PlanStatus
    trial_ends_at: datetime | None = None
    renews_at: datetime | None = None
    canceled_at: datetime | None = None
    cancel_reason: str | None = None
    can_start_trial: bool
    can_upgrade: bool
    can_cancel: bool
    support_email: str
    pro_monthly_price_usd: int
    beta_trial_days: int
    trial_days_left: int | None = None
    billing_mode: str = "internal_beta"


class BillingCancelRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=1000)
