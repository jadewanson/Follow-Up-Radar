# Iteration 05 migration correction

## Problem
The original iteration 05 migration updated `event_logs.payload_json` using JSONB operators while some local PostgreSQL installations still had the column typed as `json`. This caused `operator does not exist: json - unknown` during `alembic upgrade head`.

## Correction
The migration now explicitly converts `event_logs.payload_json` to `JSONB` before rewriting legacy `paid` status events into `item_payment_status_changed`.

## Result
- `alembic upgrade head` works on existing PostgreSQL installs coming from iter4
- `payload_json` is aligned with the authoritative baseline intent: JSONB on PostgreSQL
- lifecycle/payment split semantics remain unchanged
