# Iteration 05 — Lifecycle / Payment Split

## Purpose
Correct the domain model so that `paid` no longer closes a case. A case now has:
- one lifecycle status (`open`, `due_today`, `overdue`, `done`, `lost`, `archived`)
- one payment status (`unpaid`, `paid`, `not_applicable`)

## User-visible effects
- `Mark paid` no longer moves a case into `Closed`
- `Closed` cases now include only `done` and `lost`
- `Cases` shows a colored lifecycle badge and a plain payment status text
- item detail shows both lifecycle status and payment status

## Engineering effects
- `followup_items.payment_status` added as an authoritative field
- `item_payment_status_changed` added to the event taxonomy
- item registry now returns both lifecycle and payment state
- old event rows with `status=paid` are migrated into payment-status change events
