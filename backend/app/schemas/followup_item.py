from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.contracts.enums import ItemStatus, ItemType, PaymentStatus, ReminderStatus


def _normalize_source_url(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("source_url must be an absolute http(s) URL")
    return normalized


class ReviewSignalRead(BaseModel):
    code: str
    label: str
    severity: str


class FollowUpItemCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    client_name: str = Field(min_length=1, max_length=255)
    type: ItemType
    source_url: str | None = None
    note: str | None = None
    next_action: str | None = Field(default=None, max_length=1000)
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=8)
    due_at: datetime

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        return _normalize_source_url(value)


class FollowUpItemUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    client_name: str | None = Field(default=None, min_length=1, max_length=255)
    type: ItemType | None = None
    source_url: str | None = None
    note: str | None = None
    next_action: str | None = Field(default=None, max_length=1000)
    amount: Decimal | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=8)

    @field_validator("source_url")
    @classmethod
    def validate_source_url(cls, value: str | None) -> str | None:
        return _normalize_source_url(value)


class FollowUpItemRescheduleRequest(BaseModel):
    due_at: datetime


class FollowUpItemCompleteRequest(BaseModel):
    outcome: ItemStatus
    reason: str | None = Field(default=None, max_length=1000)


class FollowUpItemRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    client_name: str
    type: ItemType
    source_url: str | None
    note: str | None
    next_action: str | None
    done_reason: str | None
    lost_reason: str | None
    amount: Decimal | None
    currency: str | None
    due_at: datetime
    status: ItemStatus
    payment_status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    archived_at: datetime | None
    review_signals: list[ReviewSignalRead] = Field(default_factory=list)
    last_reminder_status: ReminderStatus | None = None
    last_reminder_at: datetime | None = None
    last_reminder_error: str | None = None

    model_config = {"from_attributes": True}


class FollowUpBoardResponse(BaseModel):
    overdue: list[FollowUpItemRead]
    due_today: list[FollowUpItemRead]
    scheduled: list[FollowUpItemRead]


class FollowUpRegistryEntry(BaseModel):
    id: UUID
    client_name: str
    title: str
    type: ItemType
    status: ItemStatus
    payment_status: PaymentStatus
    due_at: datetime
    amount: Decimal | None
    currency: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    next_action: str | None
    done_reason: str | None
    lost_reason: str | None
    last_event_at: datetime | None
    last_event_summary: str | None
    review_signals: list[ReviewSignalRead] = Field(default_factory=list)
    last_reminder_status: ReminderStatus | None = None
    last_reminder_at: datetime | None = None
    last_reminder_error: str | None = None


class FollowUpRegistryCounts(BaseModel):
    all: int
    active: int
    closed: int


class FollowUpRegistryResponse(BaseModel):
    scope: str
    counts: FollowUpRegistryCounts
    items: list[FollowUpRegistryEntry]


class ItemEventRead(BaseModel):
    event_type: str
    entity_type: str
    entity_id: str | None
    created_at: datetime
    summary: str


class RegistryQueryParams(BaseModel):
    scope: str = "all"
    q: str | None = None
    sort_by: str = "due_at"
    sort_dir: str = "asc"
    status: ItemStatus | None = None
    payment_status: PaymentStatus | None = None
    item_type: ItemType | None = None
    due_bucket: str | None = None
    due_from: date | None = None
    due_to: date | None = None
    amount_min: Decimal | None = None
    amount_max: Decimal | None = None
    review_signal: str | None = None
