from __future__ import annotations

from enum import Enum


class AppEnv(str, Enum):
    DEVELOPMENT = "development"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class EmailDeliveryMode(str, Enum):
    DEV_FILE = "dev_file"
    SMTP = "smtp"


class SmtpSecurity(str, Enum):
    STARTTLS = "starttls"
    SSL = "ssl"
    NONE = "none"


class Plan(str, Enum):
    FREE = "free"
    PRO = "pro"


class PlanStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


class ItemType(str, Enum):
    INVOICE = "invoice"
    PROPOSAL = "proposal"
    LEAD = "lead"
    PROMISED_REPLY = "promised_reply"
    RENEWAL = "renewal"


class ItemStatus(str, Enum):
    OPEN = "open"
    DUE_TODAY = "due_today"
    OVERDUE = "overdue"
    DONE = "done"
    LOST = "lost"
    ARCHIVED = "archived"


class PaymentStatus(str, Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    NOT_APPLICABLE = "not_applicable"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    CANCELED = "canceled"


class NotificationDeliveryKind(str, Enum):
    MAGIC_LINK_EMAIL = "magic_link_email"
    REMINDER_EMAIL = "reminder_email"
    DAILY_DIGEST_EMAIL = "daily_digest_email"


class NotificationDeliveryStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"


class EventType(str, Enum):
    AUTH_MAGIC_LINK_REQUESTED = "auth_magic_link_requested"
    AUTH_MAGIC_LINK_DELIVERED = "auth_magic_link_delivered"
    AUTH_LOGIN_SUCCESS = "auth_login_success"
    ITEM_CREATED = "item_created"
    ITEM_UPDATED = "item_updated"
    ITEM_ARCHIVED = "item_archived"
    ITEM_STATUS_CHANGED = "item_status_changed"
    ITEM_PAYMENT_STATUS_CHANGED = "item_payment_status_changed"
    ITEM_NEXT_ACTION_UPDATED = "item_next_action_updated"
    ITEM_RESCHEDULED = "item_rescheduled"
    ITEM_REOPENED = "item_reopened"
    ITEM_TEMPORAL_STATUS_RECONCILED = "item_temporal_status_reconciled"
    REMINDER_CREATED = "reminder_created"
    REMINDER_SENT = "reminder_sent"
    REMINDER_DISPATCH_FAILED = "reminder_dispatch_failed"
    DAILY_DIGEST_SENT = "daily_digest_sent"
    BILLING_TRIAL_STARTED = "billing_trial_started"
    BILLING_UPGRADED = "billing_upgraded"
    BILLING_CANCELED = "billing_canceled"


TERMINAL_ITEM_STATUSES = {
    ItemStatus.DONE,
    ItemStatus.LOST,
    ItemStatus.ARCHIVED,
}
