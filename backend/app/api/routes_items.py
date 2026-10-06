from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.contracts.enums import ItemStatus, ItemType, PaymentStatus
from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.followup_item import (
    FollowUpBoardResponse,
    FollowUpItemCompleteRequest,
    FollowUpItemCreate,
    FollowUpItemRead,
    FollowUpItemRescheduleRequest,
    FollowUpItemUpdate,
    FollowUpRegistryResponse,
    ItemEventRead,
)
from app.services.event_service import event_service
from app.services.item_service import item_service

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/board", response_model=FollowUpBoardResponse)
def get_board(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpBoardResponse:
    return item_service.board_for_user(db, user=current_user)


@router.get("/registry", response_model=FollowUpRegistryResponse)
def get_registry(
    scope: str = Query(default="all"),
    q: str | None = Query(default=None),
    sort_by: str = Query(default="due_at"),
    sort_dir: str = Query(default="asc"),
    status_filter: ItemStatus | None = Query(default=None, alias="status"),
    payment_status: PaymentStatus | None = Query(default=None),
    item_type: ItemType | None = Query(default=None),
    due_bucket: str | None = Query(default=None),
    due_from: date | None = Query(default=None),
    due_to: date | None = Query(default=None),
    amount_min: Decimal | None = Query(default=None),
    amount_max: Decimal | None = Query(default=None),
    review_signal: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> FollowUpRegistryResponse:
    return item_service.registry_for_user(
        db,
        user=current_user,
        scope=scope,
        q=q,
        sort_by=sort_by,
        sort_dir=sort_dir,
        status=status_filter,
        payment_status=payment_status,
        item_type=item_type,
        due_bucket=due_bucket,
        due_from=due_from,
        due_to=due_to,
        amount_min=amount_min,
        amount_max=amount_max,
        review_signal=review_signal,
    )


@router.post("", response_model=FollowUpItemRead, status_code=status.HTTP_201_CREATED)
def create_item(payload: FollowUpItemCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.create(db, user=current_user, payload=payload)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.get("", response_model=list[FollowUpItemRead])
def list_items(
    status_filter: ItemStatus | None = None,
    item_type: ItemType | None = None,
    include_archived: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[FollowUpItemRead]:
    items = item_service.list_for_user(db, user=current_user, status=status_filter, item_type=item_type, include_archived=include_archived)
    return [item_service.get_read(db, user=current_user, item_id=item.id) for item in items]


@router.get("/{item_id}/events", response_model=list[ItemEventRead])
def get_item_events(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> list[ItemEventRead]:
    item = item_service.get(db, user=current_user, item_id=item_id)
    events = event_service.list_for_item(db, user_id=current_user.id, item=item)
    return [
        ItemEventRead(
            event_type=event.event_type,
            entity_type=event.entity_type,
            entity_id=event.entity_id,
            created_at=event.created_at,
            summary=event_service.summarize(event),
        )
        for event in events
    ]


@router.get("/{item_id}", response_model=FollowUpItemRead)
def get_item(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    return item_service.get_read(db, user=current_user, item_id=item_id)


@router.patch("/{item_id}", response_model=FollowUpItemRead)
def update_item(item_id: str, payload: FollowUpItemUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.update(db, user=current_user, item_id=item_id, payload=payload)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.post("/{item_id}/reschedule", response_model=FollowUpItemRead)
def reschedule_item(item_id: str, payload: FollowUpItemRescheduleRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.reschedule(db, user=current_user, item_id=item_id, due_at=payload.due_at)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.post("/{item_id}/mark-paid", response_model=FollowUpItemRead)
def mark_item_paid(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.mark_paid(db, user=current_user, item_id=item_id)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.post("/{item_id}/complete", response_model=FollowUpItemRead)
def complete_item(item_id: str, payload: FollowUpItemCompleteRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.complete(db, user=current_user, item_id=item_id, outcome=payload.outcome, reason=payload.reason)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.post("/{item_id}/reopen", response_model=FollowUpItemRead)
def reopen_item(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> FollowUpItemRead:
    item = item_service.reopen(db, user=current_user, item_id=item_id)
    return item_service.get_read(db, user=current_user, item_id=item.id)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def archive_item(item_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Response:
    item_service.archive(db, user=current_user, item_id=item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
