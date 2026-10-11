# 07. Data Model and DB Schema

- **Owner role:** Architect + DB owner
- **Type of truth:** storage contract
- **Gate:** G4 / G5

## 1. Storage principles

- PostgreSQL is the production/deployment database authority.
- Schema changes are applied through Alembic migrations.
- ORM models and Alembic head must describe compatible storage.
- Nullability and delete behavior are deliberate.
- Allowed enum-like values live in backend contracts and are validated by service/API boundaries.
- Tests may use SQLite as a fast service-level substitute, but SQLite success does not replace the PostgreSQL migration gate.
- Raw magic-link secrets must never be stored in database delivery payloads.

## 2. Current tables

Alembic head currently contains:
- `users`
- `magic_link_tokens`
- `user_sessions`
- `followup_items`
- `reminders`
- `notification_deliveries`
- `subscriptions`
- `beta_interest_requests`
- `event_logs`

## 3. Key relationships

- `user_sessions.user_id -> users.id` with cascade delete
- `followup_items.user_id -> users.id` with cascade delete
- `reminders.item_id -> followup_items.id` with cascade delete
- `reminders.user_id -> users.id` with cascade delete
- `subscriptions.user_id -> users.id` with cascade delete
- nullable audit/delivery ownership may use `SET NULL` where historical records must survive account removal

## 4. Important indexed lookup paths

### users
- email

### magic_link_tokens
- email
- token hash

### user_sessions
- user
- token hash

### followup_items
- user
- due time
- lifecycle status
- payment status
- type

### reminders
- item
- user
- reminder time
- status

### notification_deliveries
- user
- kind
- idempotency key
- status

For reminder and digest deliveries, `body_text` is a retry payload. Magic-link deliveries persist a redacted marker instead of the one-time URL/token.

### subscriptions
- user

### beta_interest_requests
- user
- email

### event_logs
- user
- event type
- created time

## 5. Migration gate

A release candidate must prove from an empty PostgreSQL database that `alembic upgrade head` succeeds. A model-only `Base.metadata.create_all()` test is not a substitute for this gate.

## 6. Approved future schema addition — NOT migrated yet

[Issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) tracks a future Alembic migration for `followup_items`:
- `desired_outcome`: nullable `TEXT`.
- `expected_close_date`: nullable SQL `DATE` (not `TIMESTAMP`).

Nullability preserves existing cases. Do not add defaults that fabricate users' targets, or derive these from `due_at`, `completed_at`, or outcome reasons. Current Alembic head and ORM **do not contain these fields**. Validate upgrade of an existing PostgreSQL database, not only a fresh create. See [planned specification](34_planned_case_desired_outcome_and_expected_close_date.md).

## 7. Future outcome assessment storage — NOT migrated yet

Extend [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) with nullable `followup_items.outcome_assessment`, constrained to `exceeded`, `met`, `below` (or `NULL`). Never populate it automatically from `status`, `done_reason`, `lost_reason` or money amounts. Add an append-only closure event with assessment and a snapshot of `desired_outcome` at closing. Keep nullable for existing records and old clients; on reopen clear current value but preserve the historical event. See [planned specification](34_planned_case_desired_outcome_and_expected_close_date.md).
