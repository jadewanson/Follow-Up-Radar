# Iteration 07 — Cases Search / Sort / Filters

## Goal
Harden the `Cases` registry into a practical control surface without drifting into CRM behavior.

## What changed
- Added registry query support for:
  - `q`
  - `sort_by`
  - `sort_dir`
  - `status`
  - `payment_status`
  - `item_type`
  - `due_bucket`
  - `due_from`
  - `due_to`
  - `amount_min`
  - `amount_max`
- Added registry counts for:
  - `all`
  - `active`
  - `closed`
- Added Cases UI controls for:
  - search
  - sorting
  - filters
  - reset
- Preserved query state in the `#/cases?...` URL.

## Design boundary
This is still a follow-up case registry.
It is not a CRM, not a pipeline board, and not an arbitrary reporting builder.

## Acceptance
- Cases can be narrowed by title/client search.
- Cases can be sorted by due date, last activity, created date, amount, and client name.
- Cases can be filtered by lifecycle status, payment status, type, due bucket, due date range, and amount range.
- `All / Active / Closed` counts remain visible while filters are applied.
