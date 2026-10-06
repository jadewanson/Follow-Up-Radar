from __future__ import annotations

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.contracts.enums import ItemStatus, ItemType
from app.models.followup_item import FollowUpItem
from app.models.user import User
from app.schemas.followup_item import FollowUpItemCreate
from app.schemas.system import ActivationMilestoneRead, ActivationSummaryResponse
from app.services.item_service import item_service
from app.utils.datetime import utcnow


class ActivationService:
    def summary_for_user(self, db: Session, *, user: User) -> ActivationSummaryResponse:
        items = db.execute(
            select(FollowUpItem).where(FollowUpItem.user_id == user.id, FollowUpItem.status != ItemStatus.ARCHIVED.value)
        ).scalars().all()
        reads = [item_service._to_read_model(  # noqa: SLF001
            item=item,
            projected_status=item_service._project_status(item, now=utcnow()),  # noqa: SLF001
            latest_event_at=None,
            reminder=None,
            now=utcnow(),
        ) for item in items]
        total_cases = len(reads)
        active_cases = sum(1 for row in reads if row.status in {ItemStatus.OPEN, ItemStatus.DUE_TODAY, ItemStatus.OVERDUE})
        closed_cases = sum(1 for row in reads if row.status in {ItemStatus.DONE, ItemStatus.LOST})
        has_next_action = any(bool(row.next_action) for row in reads)
        has_review_signals = any(bool(row.review_signals) for row in reads)
        milestones = [
            ActivationMilestoneRead(code="first_case", label="Create the first case", completed=total_cases > 0),
            ActivationMilestoneRead(code="next_action", label="Set a next action", completed=has_next_action),
            ActivationMilestoneRead(code="close_case", label="Close one case with a reason", completed=closed_cases > 0),
            ActivationMilestoneRead(code="review_cases", label="Review the case registry", completed=total_cases > 1 or has_review_signals),
        ]
        if total_cases == 0:
            suggested = "Create a sample case to see the workflow end-to-end."
        elif not has_next_action:
            suggested = "Set a next action so every open case explains itself."
        elif closed_cases == 0:
            suggested = "Close one case with a reason to complete the first lifecycle."
        else:
            suggested = "Review Cases daily and clear risk signals before cases go stale."
        return ActivationSummaryResponse(
            total_cases=total_cases,
            active_cases=active_cases,
            closed_cases=closed_cases,
            has_review_signals=has_review_signals,
            milestones=milestones,
            should_show_activation=any(not milestone.completed for milestone in milestones),
            suggested_next_step=suggested,
        )

    def bootstrap_sample_case(self, db: Session, *, user: User):
        now = utcnow()
        payload = FollowUpItemCreate(
            title="Sample invoice follow-up",
            client_name="Sample client",
            type=ItemType.INVOICE,
            source_url="https://example.com/sample-invoice",
            note="This sample case shows the full Radar workflow from creation to review.",
            next_action="Send a payment reminder tomorrow",
            amount="125.00",
            currency="USD",
            due_at=now + timedelta(days=1),
        )
        return item_service.create(db, user=user, payload=payload)


activation_service = ActivationService()
