from __future__ import annotations

import uuid
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.contracts.enums import EventType, Plan, PlanStatus
from app.contracts.errors import ValidationError
from app.models.subscription import Subscription
from app.models.user import User
from app.schemas.billing import BillingSummaryResponse
from app.services.event_service import event_service
from app.utils.datetime import utcnow


class BillingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def _latest_subscription(self, db: Session, *, user_id: uuid.UUID) -> Subscription | None:
        return db.execute(
            select(Subscription).where(Subscription.user_id == user_id).order_by(Subscription.started_at.desc())
        ).scalars().first()

    def get_summary(self, db: Session, *, user: User) -> BillingSummaryResponse:
        subscription = self._latest_subscription(db, user_id=user.id)
        trial_ends_at = subscription.trial_ends_at if subscription else None
        renews_at = subscription.renews_at if subscription else None
        canceled_at = subscription.canceled_at if subscription else None
        cancel_reason = subscription.cancel_reason if subscription else None
        trial_days_left = None
        if trial_ends_at:
            delta = trial_ends_at.date() - utcnow().date()
            trial_days_left = max(delta.days, 0)
        return BillingSummaryResponse(
            plan=Plan(user.plan),
            plan_status=PlanStatus(user.plan_status),
            trial_ends_at=trial_ends_at,
            renews_at=renews_at,
            canceled_at=canceled_at,
            cancel_reason=cancel_reason,
            can_start_trial=user.plan == Plan.FREE.value,
            can_upgrade=user.plan == Plan.PRO.value and user.plan_status == PlanStatus.TRIALING.value,
            can_cancel=user.plan == Plan.PRO.value and user.plan_status in {PlanStatus.TRIALING.value, PlanStatus.ACTIVE.value},
            support_email=self.settings.support_email_address,
            pro_monthly_price_usd=self.settings.pro_monthly_price_usd,
            beta_trial_days=self.settings.beta_trial_days,
            trial_days_left=trial_days_left,
        )

    def start_trial(self, db: Session, *, user: User) -> Subscription:
        if user.plan == Plan.PRO.value and user.plan_status in {PlanStatus.TRIALING.value, PlanStatus.ACTIVE.value}:
            raise ValidationError("User already has an active Pro plan or trial")
        now = utcnow()
        trial_ends_at = now + timedelta(days=self.settings.beta_trial_days)
        subscription = self._latest_subscription(db, user_id=user.id)
        if subscription is None or subscription.status == PlanStatus.CANCELED.value:
            subscription = Subscription(
                user_id=user.id,
                provider="internal_beta",
                external_customer_id=None,
                external_subscription_id=None,
                plan=Plan.PRO.value,
                status=PlanStatus.TRIALING.value,
                started_at=now,
                renews_at=trial_ends_at,
            )
            subscription.trial_ends_at = trial_ends_at
            subscription.cancel_reason = None
            db.add(subscription)
        else:
            subscription.plan = Plan.PRO.value
            subscription.status = PlanStatus.TRIALING.value
            subscription.started_at = now
            subscription.renews_at = trial_ends_at
            subscription.trial_ends_at = trial_ends_at
            subscription.cancel_reason = None
            subscription.canceled_at = None
        user.plan = Plan.PRO.value
        user.plan_status = PlanStatus.TRIALING.value
        db.flush()
        event_service.record(
            db,
            event_type=EventType.BILLING_TRIAL_STARTED,
            entity_type="subscription",
            user_id=user.id,
            entity_id=str(subscription.id),
            payload={"trial_ends_at": trial_ends_at.isoformat()},
        )
        db.commit()
        db.refresh(subscription)
        db.refresh(user)
        return subscription

    def upgrade(self, db: Session, *, user: User) -> Subscription:
        subscription = self._latest_subscription(db, user_id=user.id)
        now = utcnow()
        if subscription is None:
            raise ValidationError("Start a beta trial before upgrading")
        subscription.plan = Plan.PRO.value
        subscription.status = PlanStatus.ACTIVE.value
        subscription.started_at = subscription.started_at or now
        subscription.renews_at = now + timedelta(days=30)
        user.plan = Plan.PRO.value
        user.plan_status = PlanStatus.ACTIVE.value
        event_service.record(
            db,
            event_type=EventType.BILLING_UPGRADED,
            entity_type="subscription",
            user_id=user.id,
            entity_id=str(subscription.id),
            payload={"renews_at": subscription.renews_at.isoformat()},
        )
        db.commit()
        db.refresh(subscription)
        db.refresh(user)
        return subscription

    def cancel(self, db: Session, *, user: User, reason: str) -> Subscription:
        subscription = self._latest_subscription(db, user_id=user.id)
        if subscription is None or subscription.status not in {PlanStatus.TRIALING.value, PlanStatus.ACTIVE.value}:
            raise ValidationError("No active trial or plan to cancel")
        now = utcnow()
        subscription.status = PlanStatus.CANCELED.value
        subscription.canceled_at = now
        subscription.cancel_reason = reason.strip()
        user.plan = Plan.FREE.value
        user.plan_status = PlanStatus.ACTIVE.value
        event_service.record(
            db,
            event_type=EventType.BILLING_CANCELED,
            entity_type="subscription",
            user_id=user.id,
            entity_id=str(subscription.id),
            payload={"reason": reason.strip()},
        )
        db.commit()
        db.refresh(subscription)
        db.refresh(user)
        return subscription


billing_service = BillingService()
