from __future__ import annotations

import uuid
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.contracts.enums import (
    EventType,
    ItemStatus,
    ItemType,
    PaymentStatus,
    ReminderStatus,
    TERMINAL_ITEM_STATUSES,
)
from app.contracts.errors import NotFoundError, ValidationError
from app.domain.item_state_machine import (
    ensure_archivable,
    ensure_mutable_status,
    ensure_terminal_transition,
    reconcile_temporal_status,
)
from app.models.followup_item import FollowUpItem
from app.models.reminder import Reminder
from app.models.user import User
from app.schemas.followup_item import (
    FollowUpBoardResponse,
    FollowUpItemCreate,
    FollowUpItemRead,
    FollowUpItemUpdate,
    FollowUpRegistryCounts,
    FollowUpRegistryEntry,
    FollowUpRegistryResponse,
    ReviewSignalRead,
)
from app.services.event_service import event_service
from app.services.reminder_service import reminder_service
from app.utils.datetime import coerce_utc, utcnow

ACTIVE_STATUSES = {ItemStatus.OPEN, ItemStatus.DUE_TODAY, ItemStatus.OVERDUE}
CLOSED_STATUSES = {ItemStatus.DONE, ItemStatus.LOST}
REGISTRY_SORT_FIELDS = {"due_at", "last_activity", "created_at", "amount", "client_name"}
REGISTRY_SORT_DIRS = {"asc", "desc"}
REGISTRY_DUE_BUCKETS = {"overdue", "due_today", "scheduled"}
REGISTRY_SCOPES = {"all", "active", "closed"}
REGISTRY_REVIEW_SIGNALS = {
    "needs_action",
    "paid_but_open",
    "stale_case",
    "reminder_failed",
    "overdue_without_reminder",
    "reminder_issue",
}


class ItemService:
    def _normalize_due_at(self, due_at: datetime) -> datetime:
        return coerce_utc(due_at)

    def _normalize_currency(self, currency: str | None) -> str | None:
        if currency is None:
            return None
        normalized = currency.strip().upper()
        if len(normalized) < 3 or len(normalized) > 8:
            raise ValidationError("currency must be 3 to 8 characters")
        return normalized

    def _normalize_text(self, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    def _default_payment_status(self, item_type: ItemType) -> PaymentStatus:
        if item_type in {ItemType.INVOICE, ItemType.RENEWAL}:
            return PaymentStatus.UNPAID
        return PaymentStatus.NOT_APPLICABLE

    def _coerce_uuid(self, value: uuid.UUID | str) -> uuid.UUID:
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))

    def _owned_item_or_die(self, db: Session, *, item_id: uuid.UUID | str, user_id: uuid.UUID | str) -> FollowUpItem:
        item = db.execute(
            select(FollowUpItem).where(
                FollowUpItem.id == self._coerce_uuid(item_id),
                FollowUpItem.user_id == self._coerce_uuid(user_id),
            )
        ).scalar_one_or_none()
        if item is None:
            raise NotFoundError("Follow-up item not found")
        return item

    def _project_status(self, item: FollowUpItem, *, now: datetime | None = None) -> ItemStatus:
        current = ItemStatus(item.status)
        if current in TERMINAL_ITEM_STATUSES:
            return current
        return reconcile_temporal_status(current, item.due_at, now)

    def _validate_registry_scope(self, scope: str) -> str:
        normalized = scope.strip().lower()
        if normalized not in REGISTRY_SCOPES:
            raise ValidationError("registry scope must be one of: all, active, closed")
        return normalized

    def _validate_sorting(self, sort_by: str, sort_dir: str) -> tuple[str, str]:
        normalized_sort_by = sort_by.strip().lower()
        normalized_sort_dir = sort_dir.strip().lower()
        if normalized_sort_by not in REGISTRY_SORT_FIELDS:
            raise ValidationError("sort_by must be one of: due_at, last_activity, created_at, amount, client_name")
        if normalized_sort_dir not in REGISTRY_SORT_DIRS:
            raise ValidationError("sort_dir must be one of: asc, desc")
        return normalized_sort_by, normalized_sort_dir

    def _validate_due_bucket(self, due_bucket: str | None) -> str | None:
        if due_bucket is None or due_bucket == "":
            return None
        normalized = due_bucket.strip().lower()
        if normalized not in REGISTRY_DUE_BUCKETS:
            raise ValidationError("due_bucket must be one of: overdue, due_today, scheduled")
        return normalized

    def _validate_review_signal(self, review_signal: str | None) -> str | None:
        if review_signal is None or review_signal == "":
            return None
        normalized = review_signal.strip().lower()
        if normalized not in REGISTRY_REVIEW_SIGNALS:
            raise ValidationError(
                "review_signal must be one of: needs_action, paid_but_open, stale_case, reminder_failed, overdue_without_reminder, reminder_issue"
            )
        return normalized

    def _registry_scope_match(self, status: ItemStatus, scope: str) -> bool:
        if scope == "all":
            return True
        if scope == "active":
            return status in ACTIVE_STATUSES
        return status in CLOSED_STATUSES

    def _registry_due_bucket_match(self, status: ItemStatus, due_bucket: str | None) -> bool:
        if due_bucket is None:
            return True
        if due_bucket == "scheduled":
            return status == ItemStatus.OPEN
        if due_bucket == "due_today":
            return status == ItemStatus.DUE_TODAY
        return status == ItemStatus.OVERDUE

    def _registry_amount_match(self, amount: Decimal | None, amount_min: Decimal | None, amount_max: Decimal | None) -> bool:
        if amount_min is None and amount_max is None:
            return True
        if amount is None:
            return False
        if amount_min is not None and amount < amount_min:
            return False
        if amount_max is not None and amount > amount_max:
            return False
        return True

    def _registry_date_match(self, due_at: datetime, due_from: date | None, due_to: date | None) -> bool:
        due_date = coerce_utc(due_at).date()
        if due_from is not None and due_date < due_from:
            return False
        if due_to is not None and due_date > due_to:
            return False
        return True

    def _registry_search_match(self, item: FollowUpItem, query: str | None) -> bool:
        if not query:
            return True
        needle = query.strip().lower()
        if not needle:
            return True
        haystacks = [item.client_name, item.title, item.next_action or ""]
        return any(needle in value.lower() for value in haystacks)

    def _sort_registry_entries(self, entries: list[FollowUpRegistryEntry], *, sort_by: str, sort_dir: str) -> list[FollowUpRegistryEntry]:
        reverse = sort_dir == "desc"

        def sort_key(entry: FollowUpRegistryEntry):
            if sort_by == "due_at":
                return entry.due_at
            if sort_by == "last_activity":
                return entry.last_event_at or entry.updated_at or entry.created_at
            if sort_by == "created_at":
                return entry.created_at
            if sort_by == "amount":
                return (entry.amount is None, entry.amount or Decimal("0"))
            return entry.client_name.lower()

        return sorted(entries, key=sort_key, reverse=reverse)

    def _latest_reminders_for_items(self, db: Session, *, items: list[FollowUpItem]) -> dict[str, Reminder]:
        item_ids = {item.id for item in items}
        if not item_ids:
            return {}
        reminders = db.execute(
            select(Reminder).where(Reminder.item_id.in_(item_ids)).order_by(Reminder.created_at.desc())
        ).scalars().all()
        latest: dict[str, Reminder] = {}
        for reminder in reminders:
            item_id = str(reminder.item_id)
            if item_id in latest:
                continue
            latest[item_id] = reminder
        return latest

    def _reminder_state_snapshot(self, reminder: Reminder | None) -> tuple[ReminderStatus | None, datetime | None, str | None]:
        if reminder is None:
            return None, None, None
        at = reminder.sent_at or reminder.last_attempt_at or reminder.reminder_at
        return ReminderStatus(reminder.status), at, reminder.last_error

    def _review_signals_for_item(
        self,
        *,
        item: FollowUpItem,
        projected_status: ItemStatus,
        latest_event_at: datetime | None,
        reminder: Reminder | None,
        now: datetime,
    ) -> list[ReviewSignalRead]:
        signals: list[ReviewSignalRead] = []
        if projected_status in {ItemStatus.OVERDUE, ItemStatus.DUE_TODAY}:
            signals.append(
                ReviewSignalRead(
                    code="needs_action",
                    label="Needs action",
                    severity="critical" if projected_status == ItemStatus.OVERDUE else "warning",
                )
            )
        if PaymentStatus(item.payment_status) == PaymentStatus.PAID and projected_status in ACTIVE_STATUSES:
            signals.append(ReviewSignalRead(code="paid_but_open", label="Paid but open", severity="warning"))
        activity_at = latest_event_at or item.updated_at or item.created_at
        if projected_status in ACTIVE_STATUSES and now - coerce_utc(activity_at) >= timedelta(days=7):
            signals.append(ReviewSignalRead(code="stale_case", label="No activity 7+ days", severity="warning"))
        if reminder is not None and ReminderStatus(reminder.status) == ReminderStatus.FAILED:
            signals.append(ReviewSignalRead(code="reminder_failed", label="Reminder failed", severity="critical"))
        if projected_status == ItemStatus.OVERDUE and (reminder is None or ReminderStatus(reminder.status) in {ReminderStatus.PENDING, ReminderStatus.FAILED, ReminderStatus.CANCELED}):
            signals.append(ReviewSignalRead(code="overdue_without_reminder", label="Overdue without reminder", severity="warning"))
        if any(signal.code in {"reminder_failed", "overdue_without_reminder"} for signal in signals):
            signals.append(ReviewSignalRead(code="reminder_issue", label="Reminder issue", severity="info"))
        deduped: dict[str, ReviewSignalRead] = {}
        for signal in signals:
            deduped.setdefault(signal.code, signal)
        return list(deduped.values())

    def _entry_matches_review_signal(self, review_signals: list[ReviewSignalRead], review_signal: str | None) -> bool:
        if review_signal is None:
            return True
        return any(signal.code == review_signal for signal in review_signals)

    def _to_read_model(
        self,
        *,
        item: FollowUpItem,
        projected_status: ItemStatus,
        latest_event_at: datetime | None,
        reminder: Reminder | None,
        now: datetime,
    ) -> FollowUpItemRead:
        reminder_status, reminder_at, reminder_error = self._reminder_state_snapshot(reminder)
        review_signals = self._review_signals_for_item(
            item=item,
            projected_status=projected_status,
            latest_event_at=latest_event_at,
            reminder=reminder,
            now=now,
        )
        return FollowUpItemRead(
            id=item.id,
            user_id=item.user_id,
            title=item.title,
            client_name=item.client_name,
            type=ItemType(item.type),
            source_url=item.source_url,
            note=item.note,
            next_action=item.next_action,
            done_reason=item.done_reason,
            lost_reason=item.lost_reason,
            amount=item.amount,
            currency=item.currency,
            due_at=item.due_at,
            status=projected_status,
            payment_status=PaymentStatus(item.payment_status),
            created_at=item.created_at,
            updated_at=item.updated_at,
            completed_at=item.completed_at,
            archived_at=item.archived_at,
            review_signals=review_signals,
            last_reminder_status=reminder_status,
            last_reminder_at=reminder_at,
            last_reminder_error=reminder_error,
        )

    def _to_registry_entry(
        self,
        *,
        item: FollowUpItem,
        projected_status: ItemStatus,
        latest_event_summary: str | None,
        latest_event_at: datetime | None,
        reminder: Reminder | None,
        now: datetime,
    ) -> FollowUpRegistryEntry:
        reminder_status, reminder_at, reminder_error = self._reminder_state_snapshot(reminder)
        review_signals = self._review_signals_for_item(
            item=item,
            projected_status=projected_status,
            latest_event_at=latest_event_at,
            reminder=reminder,
            now=now,
        )
        return FollowUpRegistryEntry(
            id=item.id,
            client_name=item.client_name,
            title=item.title,
            type=ItemType(item.type),
            status=projected_status,
            payment_status=PaymentStatus(item.payment_status),
            due_at=item.due_at,
            amount=item.amount,
            currency=item.currency,
            created_at=item.created_at,
            updated_at=item.updated_at,
            completed_at=item.completed_at,
            next_action=item.next_action,
            done_reason=item.done_reason,
            lost_reason=item.lost_reason,
            last_event_at=latest_event_at,
            last_event_summary=latest_event_summary,
            review_signals=review_signals,
            last_reminder_status=reminder_status,
            last_reminder_at=reminder_at,
            last_reminder_error=reminder_error,
        )

    def create(self, db: Session, *, user: User, payload: FollowUpItemCreate) -> FollowUpItem:
        due_at = self._normalize_due_at(payload.due_at)
        now = utcnow()
        status = reconcile_temporal_status(ItemStatus.OPEN, due_at, now)
        payment_status = self._default_payment_status(payload.type)
        normalized_next_action = self._normalize_text(payload.next_action)

        item = FollowUpItem(
            user_id=user.id,
            title=payload.title.strip(),
            client_name=payload.client_name.strip(),
            type=payload.type.value,
            source_url=payload.source_url,
            note=payload.note,
            next_action=normalized_next_action,
            amount=payload.amount,
            currency=self._normalize_currency(payload.currency),
            due_at=due_at,
            status=status.value,
            payment_status=payment_status.value,
            created_at=now,
            updated_at=now,
        )

        try:
            db.add(item)
            db.flush()
            reminder_service.create_for_item(db, item=item)
            event_service.record(
                db,
                event_type=EventType.ITEM_CREATED,
                entity_type="followup_item",
                user_id=user.id,
                entity_id=str(item.id),
                payload={
                    "type": item.type,
                    "status": item.status,
                    "payment_status": item.payment_status,
                    "due_at": coerce_utc(item.due_at).isoformat(),
                    "next_action": item.next_action,
                },
            )
            if item.next_action:
                event_service.record(
                    db,
                    event_type=EventType.ITEM_NEXT_ACTION_UPDATED,
                    entity_type="followup_item",
                    user_id=user.id,
                    entity_id=str(item.id),
                    payload={"next_action": item.next_action},
                )
            db.commit()
        except Exception:
            db.rollback()
            raise
        db.refresh(item)
        return item

    def list_for_user(
        self,
        db: Session,
        *,
        user: User,
        status: ItemStatus | None = None,
        item_type: ItemType | None = None,
        include_archived: bool = False,
    ) -> list[FollowUpItem]:
        stmt: Select[tuple[FollowUpItem]] = select(FollowUpItem).where(FollowUpItem.user_id == user.id)
        if not include_archived:
            stmt = stmt.where(FollowUpItem.status != ItemStatus.ARCHIVED.value)
        if status is not None:
            stmt = stmt.where(FollowUpItem.status == status.value)
        if item_type is not None:
            stmt = stmt.where(FollowUpItem.type == item_type.value)
        return db.execute(stmt.order_by(FollowUpItem.due_at.asc(), FollowUpItem.created_at.desc())).scalars().all()

    def list_active_for_all_users(self, db: Session) -> list[FollowUpItem]:
        stmt: Select[tuple[FollowUpItem]] = select(FollowUpItem).where(FollowUpItem.status != ItemStatus.ARCHIVED.value)
        return db.execute(stmt.order_by(FollowUpItem.due_at.asc(), FollowUpItem.created_at.desc())).scalars().all()

    def get(self, db: Session, *, user: User, item_id: uuid.UUID | str) -> FollowUpItem:
        return self._owned_item_or_die(db, item_id=item_id, user_id=user.id)

    def get_read(self, db: Session, *, user: User, item_id: uuid.UUID | str) -> FollowUpItemRead:
        item = self.get(db, user=user, item_id=item_id)
        now = utcnow()
        latest_event = event_service.latest_for_items(db, user_id=user.id, items=[item]).get(str(item.id))
        latest_reminder = self._latest_reminders_for_items(db, items=[item]).get(str(item.id))
        return self._to_read_model(
            item=item,
            projected_status=self._project_status(item, now=now),
            latest_event_at=latest_event.created_at if latest_event else None,
            reminder=latest_reminder,
            now=now,
        )

    def update(self, db: Session, *, user: User, item_id: uuid.UUID | str, payload: FollowUpItemUpdate) -> FollowUpItem:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        ensure_mutable_status(ItemStatus(item.status))
        fields = payload.model_fields_set
        previous_next_action = item.next_action

        if "title" in fields:
            item.title = payload.title.strip() if payload.title is not None else item.title
        if "client_name" in fields:
            item.client_name = payload.client_name.strip() if payload.client_name is not None else item.client_name
        if "type" in fields and payload.type is not None:
            item.type = payload.type.value
            default_payment_status = self._default_payment_status(payload.type)
            if default_payment_status == PaymentStatus.NOT_APPLICABLE:
                item.payment_status = default_payment_status.value
            elif item.payment_status == PaymentStatus.NOT_APPLICABLE.value:
                item.payment_status = default_payment_status.value
        if "source_url" in fields:
            item.source_url = payload.source_url
        if "note" in fields:
            item.note = payload.note
        if "next_action" in fields:
            item.next_action = self._normalize_text(payload.next_action)
        if "amount" in fields:
            item.amount = payload.amount
        if "currency" in fields:
            item.currency = self._normalize_currency(payload.currency)

        item.updated_at = utcnow()
        event_service.record(
            db,
            event_type=EventType.ITEM_UPDATED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload={"status": item.status, "payment_status": item.payment_status},
        )
        if item.next_action != previous_next_action:
            event_service.record(
                db,
                event_type=EventType.ITEM_NEXT_ACTION_UPDATED,
                entity_type="followup_item",
                user_id=user.id,
                entity_id=str(item.id),
                payload={"next_action": item.next_action},
            )
        db.commit()
        db.refresh(item)
        return item

    def reschedule(self, db: Session, *, user: User, item_id: uuid.UUID | str, due_at: datetime) -> FollowUpItem:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        ensure_mutable_status(ItemStatus(item.status))
        normalized_due_at = self._normalize_due_at(due_at)
        item.due_at = normalized_due_at
        item.status = reconcile_temporal_status(ItemStatus.OPEN, normalized_due_at).value
        item.updated_at = utcnow()
        reminder_service.update_pending_for_item(db, item=item)
        event_service.record(
            db,
            event_type=EventType.ITEM_RESCHEDULED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload={"due_at": coerce_utc(item.due_at).isoformat(), "status": item.status},
        )
        db.commit()
        db.refresh(item)
        return item

    def mark_paid(self, db: Session, *, user: User, item_id: uuid.UUID | str) -> FollowUpItem:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        ensure_mutable_status(ItemStatus(item.status))
        if PaymentStatus(item.payment_status) == PaymentStatus.NOT_APPLICABLE:
            raise ValidationError("Payment is not applicable for this case")
        if PaymentStatus(item.payment_status) == PaymentStatus.PAID:
            raise ValidationError("Item is already marked paid")
        item.payment_status = PaymentStatus.PAID.value
        item.updated_at = utcnow()
        event_service.record(
            db,
            event_type=EventType.ITEM_PAYMENT_STATUS_CHANGED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload={"payment_status": item.payment_status},
        )
        db.commit()
        db.refresh(item)
        return item

    def complete(
        self,
        db: Session,
        *,
        user: User,
        item_id: uuid.UUID | str,
        outcome: ItemStatus,
        reason: str | None = None,
    ) -> FollowUpItem:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        ensure_terminal_transition(ItemStatus(item.status), outcome)
        now = utcnow()
        normalized_reason = self._normalize_text(reason)
        if outcome in {ItemStatus.DONE, ItemStatus.LOST} and not normalized_reason:
            raise ValidationError(f"reason is required when marking case {outcome.value}")
        item.status = outcome.value
        item.completed_at = now
        item.updated_at = now
        item.next_action = None
        if outcome == ItemStatus.DONE:
            item.done_reason = normalized_reason
            item.lost_reason = None
        elif outcome == ItemStatus.LOST:
            item.lost_reason = normalized_reason
            item.done_reason = None
        reminder_service.cancel_pending_for_item(db, item_id=str(item.id))
        payload = {"status": item.status}
        if normalized_reason:
            payload["reason"] = normalized_reason
        event_service.record(
            db,
            event_type=EventType.ITEM_STATUS_CHANGED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload=payload,
        )
        db.commit()
        db.refresh(item)
        return item

    def reopen(self, db: Session, *, user: User, item_id: uuid.UUID | str) -> FollowUpItem:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        current = ItemStatus(item.status)
        if current not in {ItemStatus.DONE, ItemStatus.LOST}:
            raise ValidationError("Only done or lost cases can be reopened")
        now = utcnow()
        projected = reconcile_temporal_status(ItemStatus.OPEN, item.due_at, now)
        item.status = projected.value
        item.completed_at = None
        item.updated_at = now
        event_service.record(
            db,
            event_type=EventType.ITEM_REOPENED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload={"status": item.status},
        )
        db.commit()
        db.refresh(item)
        return item

    def archive(self, db: Session, *, user: User, item_id: uuid.UUID | str) -> None:
        item = self._owned_item_or_die(db, item_id=item_id, user_id=user.id)
        ensure_archivable(ItemStatus(item.status))
        now = utcnow()
        item.status = ItemStatus.ARCHIVED.value
        item.archived_at = now
        item.updated_at = now
        reminder_service.cancel_pending_for_item(db, item_id=str(item.id))
        event_service.record(
            db,
            event_type=EventType.ITEM_ARCHIVED,
            entity_type="followup_item",
            user_id=user.id,
            entity_id=str(item.id),
            payload={"archived_at": now.isoformat()},
        )
        db.commit()

    def reconcile_temporal_statuses(self, db: Session, *, items: Iterable[FollowUpItem] | None = None) -> int:
        now = utcnow()
        changed = 0
        candidates = list(items) if items is not None else self.list_active_for_all_users(db)
        for item in candidates:
            current = ItemStatus(item.status)
            projected = self._project_status(item, now=now)
            if projected == current:
                continue
            item.status = projected.value
            item.updated_at = now
            changed += 1
            event_service.record(
                db,
                event_type=EventType.ITEM_TEMPORAL_STATUS_RECONCILED,
                entity_type="followup_item",
                user_id=item.user_id,
                entity_id=str(item.id),
                payload={"status": projected.value},
            )
        if changed:
            db.commit()
        return changed

    def registry_for_user(
        self,
        db: Session,
        *,
        user: User,
        scope: str = "all",
        q: str | None = None,
        sort_by: str = "due_at",
        sort_dir: str = "asc",
        status: ItemStatus | None = None,
        payment_status: PaymentStatus | None = None,
        item_type: ItemType | None = None,
        due_bucket: str | None = None,
        due_from: date | None = None,
        due_to: date | None = None,
        amount_min: Decimal | None = None,
        amount_max: Decimal | None = None,
        review_signal: str | None = None,
    ) -> FollowUpRegistryResponse:
        normalized_scope = self._validate_registry_scope(scope)
        normalized_sort_by, normalized_sort_dir = self._validate_sorting(sort_by, sort_dir)
        normalized_due_bucket = self._validate_due_bucket(due_bucket)
        normalized_review_signal = self._validate_review_signal(review_signal)

        stmt: Select[tuple[FollowUpItem]] = select(FollowUpItem).where(
            FollowUpItem.user_id == user.id,
            FollowUpItem.status != ItemStatus.ARCHIVED.value,
        )
        items = db.execute(stmt).scalars().all()
        latest_events = event_service.latest_for_items(db, user_id=user.id, items=items)
        latest_reminders = self._latest_reminders_for_items(db, items=items)
        now = utcnow()

        matched_entries: list[FollowUpRegistryEntry] = []
        for item in items:
            projected_status = self._project_status(item, now=now)
            if status is not None and projected_status != status:
                continue
            if payment_status is not None and PaymentStatus(item.payment_status) != payment_status:
                continue
            if item_type is not None and ItemType(item.type) != item_type:
                continue
            if not self._registry_due_bucket_match(projected_status, normalized_due_bucket):
                continue
            if not self._registry_search_match(item, q):
                continue
            if not self._registry_amount_match(item.amount, amount_min, amount_max):
                continue
            if not self._registry_date_match(item.due_at, due_from, due_to):
                continue

            latest = latest_events.get(str(item.id))
            reminder = latest_reminders.get(str(item.id))
            entry = self._to_registry_entry(
                item=item,
                projected_status=projected_status,
                latest_event_summary=event_service.summarize(latest) if latest else None,
                latest_event_at=latest.created_at if latest else None,
                reminder=reminder,
                now=now,
            )
            if not self._entry_matches_review_signal(entry.review_signals, normalized_review_signal):
                continue
            matched_entries.append(entry)

        counts = FollowUpRegistryCounts(
            all=len(matched_entries),
            active=sum(1 for entry in matched_entries if entry.status in ACTIVE_STATUSES),
            closed=sum(1 for entry in matched_entries if entry.status in CLOSED_STATUSES),
        )
        scoped_entries = [entry for entry in matched_entries if self._registry_scope_match(entry.status, normalized_scope)]
        scoped_entries = self._sort_registry_entries(scoped_entries, sort_by=normalized_sort_by, sort_dir=normalized_sort_dir)
        return FollowUpRegistryResponse(scope=normalized_scope, counts=counts, items=scoped_entries)

    def board_for_user(self, db: Session, *, user: User) -> FollowUpBoardResponse:
        items = self.list_for_user(db, user=user)
        latest_events = event_service.latest_for_items(db, user_id=user.id, items=items)
        latest_reminders = self._latest_reminders_for_items(db, items=items)
        now = utcnow()
        overdue: list[FollowUpItemRead] = []
        due_today: list[FollowUpItemRead] = []
        scheduled: list[FollowUpItemRead] = []
        for item in items:
            projected = self._project_status(item, now=now)
            read_model = self._to_read_model(
                item=item,
                projected_status=projected,
                latest_event_at=latest_events.get(str(item.id)).created_at if latest_events.get(str(item.id)) else None,
                reminder=latest_reminders.get(str(item.id)),
                now=now,
            )
            if projected == ItemStatus.OVERDUE:
                overdue.append(read_model)
            elif projected == ItemStatus.DUE_TODAY:
                due_today.append(read_model)
            elif projected == ItemStatus.OPEN:
                scheduled.append(read_model)
        overdue.sort(key=lambda entry: entry.due_at)
        due_today.sort(key=lambda entry: entry.due_at)
        scheduled.sort(key=lambda entry: entry.due_at)
        return FollowUpBoardResponse(overdue=overdue, due_today=due_today, scheduled=scheduled)


item_service = ItemService()
