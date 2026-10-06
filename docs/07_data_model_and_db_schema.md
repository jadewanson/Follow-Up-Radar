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
