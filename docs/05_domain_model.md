# 05. Domain Model

- **Owner role:** Architect
- **Type of truth:** current domain model
- **Gate:** G3 / G4 / G5

This document describes the current iteration-14 model. Later iteration notes may explain how the model evolved, but they do not override this file.

## 1. Core invariants

- A follow-up case has **one lifecycle status** and **one payment status**.
- Lifecycle status is one of: `open`, `due_today`, `overdue`, `done`, `lost`, `archived`.
- Payment status is one of: `unpaid`, `paid`, `not_applicable`.
- `paid` is not a lifecycle state and does not close a case.
- PostgreSQL-backed models are authoritative for persisted domain state.
- Web and extension clients do not own domain state.
- One-time authentication secrets are never persisted in notification message bodies.

## 2. Entities

### User
Account owner.

Required persisted fields:
- `id`
- `email`
- `timezone`
- `plan`
- `plan_status`
- `created_at`

### MagicLinkToken
One sign-in challenge.

Fields:
- `id`
- `email`
- `token_hash`
- `expires_at`
- `consumed_at`
- `created_at`

The raw token exists only long enough to construct and deliver the sign-in message. Only its keyed hash is persisted.

### UserSession
One authenticated bearer session.

Fields:
- `id`
- `user_id`
- `token_hash`
- `expires_at`
- `revoked_at`
- `created_at`
- `last_seen_at`

### FollowUpItem
One client or money follow-up obligation.

Fields:
- `id`
- `user_id`
- `title`
- `client_name`
- `type`
- `source_url`
- `note`
- `next_action`
- `done_reason`
- `lost_reason`
- `amount`
- `currency`
- `due_at`
- `status`
- `payment_status`
- `created_at`
- `updated_at`
- `completed_at`
- `archived_at`

### Approved FollowUpItem extension — planned, NOT present in iteration-14 model

- `desired_outcome`: optional user-authored text describing the intended business result.
- `expected_close_date`: optional **date-only** value for the user's expected case closure day (not a reminder timestamp).

These are **planned fields**, excluded from the current persisted field list above until [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) is implemented. They are distinct from `next_action`, `due_at`, `completed_at`, `done_reason` and `lost_reason`. See [implementation specification](34_planned_case_desired_outcome_and_expected_close_date.md). Until then existing code/schema remain unchanged and are not in conflict with this *future* extension.

### Reminder
Scheduled delivery intent for one case.

Fields:
- `id`
- `item_id`
- `user_id`
- `reminder_at`
- `status`
- `attempt_count`
- `last_attempt_at`
- `last_error`
- `sent_at`
- `clicked_at`
- `canceled_at`
- `created_at`

### NotificationDelivery
Durable delivery record used for magic-link, reminder, and daily-digest messages.

Fields:
- `id`
- `user_id`
- `kind`
- `idempotency_key`
- `related_entity_type`
- `related_entity_id`
- `to_email`
- `subject`
- `body_text`
- `provider`
- `status`
- `provider_message_id`
- `error_text`
- `attempt_count`
- `sent_at`
- `created_at`
- `updated_at`

For ordinary reminder and digest messages, `body_text` is the durable retry payload. For a magic-link message it contains only a redacted audit marker. The one-time login URL/token is supplied directly to the configured gateway and is not recoverable from this table.

### Subscription
Current internal-beta subscription state. It does **not** represent a real charged payment-provider subscription yet.

Fields:
- `id`
- `user_id`
- `provider`
- `external_customer_id`
- `external_subscription_id`
- `plan`
- `status`
- `started_at`
- `renews_at`
- `trial_ends_at`
- `canceled_at`
- `cancel_reason`

### BetaInterestRequest
Public beta-interest submission.

Fields:
- `id`
- `user_id`
- `email`
- `source`
- `note`
- `created_at`

### EventLog
Append-only record of domain facts used for case history and review signals.

Fields:
- `id`
- `user_id`
- `event_type`
- `entity_type`
- `entity_id`
- `payload_json`
- `created_at`

## 3. Authority rule

When this document, an iteration note, and executable code disagree, treat the mismatch as a defect. Current models, contracts, migrations, tests, and this document must converge on the same semantics before a release gate can pass.

### Planned completion assessment (NOT current iteration-14 model)

- `outcome_assessment`: nullable, user-selected comparison (`exceeded`, `met`, `below`) at explicit `done`/`lost` closure, meaningful only when `desired_outcome` exists.
- Not a lifecycle state, payment status, or substitute for `done_reason` / `lost_reason`.
- Historical completion events must capture assessment and the desired-outcome text as it existed at that closure; reopening clears the current assessment but preserves event history.
- Requires new migration, API/domain work and UI; tracked in [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6). See [planned specification](34_planned_case_desired_outcome_and_expected_close_date.md).
