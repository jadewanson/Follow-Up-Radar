# 06. State Machine

- **Owner role:** Architect + Tech Lead
- **Type of truth:** authoritative lifecycle behavior
- **Gate:** G3 / G5 / G10

## 1. Two independent state axes

### Lifecycle status
Only:
- `open`
- `due_today`
- `overdue`
- `done`
- `lost`
- `archived`

### Payment status
Only:
- `unpaid`
- `paid`
- `not_applicable`

`paid` is not a lifecycle status. Marking an invoice or renewal paid does not close it.

## 2. Lifecycle semantics

- **open:** active case due after the current UTC date.
- **due_today:** active case due on the current UTC date.
- **overdue:** active case due before the current UTC date.
- **done:** terminal successful lifecycle outcome.
- **lost:** terminal unsuccessful lifecycle outcome.
- **archived:** hidden/inactive case.

For non-terminal cases, `open` / `due_today` / `overdue` are projected from `due_at` and current UTC time.

## 3. Allowed operations

### Create
Creates an active case and its initial reminder in the same authoritative flow.

### Reschedule
Allowed only for active cases. Updating `due_at` recomputes the active lifecycle status and updates or recreates a pending reminder.

Examples:
- `overdue -> open`
- `open -> due_today`
- `due_today -> overdue`

### Mark paid
Allowed only when payment is applicable and the case is mutable. Changes `payment_status` to `paid`; lifecycle status is unchanged.

### Complete
Allowed only from a non-terminal lifecycle state:
- active -> `done`
- active -> `lost`

A non-empty outcome reason is required. Completion clears `next_action` and cancels pending reminders.

### Reopen
Allowed only from `done` or `lost`.

Reopen:
- clears `completed_at`;
- projects the new active status from `due_at`;
- does not restore the previous `next_action`;
- re-arms reminder coverage for the reopened case.

### Archive
Allowed from any non-archived lifecycle state. Archiving cancels pending reminders.

## 4. Forbidden operations

Examples:
- completing an already terminal case;
- rescheduling `done`, `lost`, or `archived`;
- marking payment on `not_applicable` cases;
- reopening `open`, `due_today`, `overdue`, or `archived`;
- archiving an already archived case.

Forbidden operations return explicit domain errors.

## 5. State authority

Lifecycle and payment state can be mutated only by backend service flows. Clients may display projected state but do not authoritatively infer or write state outside the API.

## 6. Test requirements

The suite must cover:
- active temporal projection;
- close with required reasons;
- payment/lifecycle separation;
- reschedule reminder behavior;
- reopen plus reminder re-arming;
- forbidden terminal mutations;
- archive behavior.

## 7. Approved future case-planning metadata — not implemented

[Issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) introduces planned fields `desired_outcome` and `expected_close_date`. They are *descriptive target metadata*, not new lifecycle states or triggers:
- Neither field changes `status`, `payment_status`, `due_at`, `completed_at` or reminder scheduling by itself.
- Passing `expected_close_date` does not automatically close, mark lost, or archive the case.
- Explicit closure with `done`/`lost` and a non-empty actual reason remains required.
- Both targets survive closure as planned intent, distinct from actual outcome.

These requirements apply **when implemented**, not to the present build. See [planned specification](34_planned_case_desired_outcome_and_expected_close_date.md).
