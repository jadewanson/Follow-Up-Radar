from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class PublicSiteConfigResponse(BaseModel):
    product_name: str
    tagline: str
    support_email: str
    beta_trial_days: int
    pro_monthly_price_usd: int
    free_plan_name: str
    pro_plan_name: str
    beta_message: str


class BetaInterestRequestCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    note: str | None = Field(default=None, max_length=2000)
    source: str = Field(default="pricing", min_length=1, max_length=64)


class BetaInterestResponse(BaseModel):
    status: str
    created_at: datetime


class ActivationMilestoneRead(BaseModel):
    code: str
    label: str
    completed: bool


class ActivationSummaryResponse(BaseModel):
    total_cases: int
    active_cases: int
    closed_cases: int
    has_review_signals: bool
    milestones: list[ActivationMilestoneRead]
    should_show_activation: bool
    suggested_next_step: str
