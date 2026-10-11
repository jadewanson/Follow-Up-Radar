# Planned Feature — Case Desired Outcome and Expected Close Date

- **Status:** APPROVED PRODUCT REQUIREMENT — TO IMPLEMENT; **NOT PRESENT** in current iteration-14 code, database, API or web UI.
- **Tracking:** [GitHub issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6).
- **Decision record:** [ADR-005](17_decision_log_seed.md).
- **Purpose:** let a user record both the business goal of a case and the date by which that goal is expected to be resolved.

## 1. Business requirement

The user can specify two separate planning facts **when creating a case** and maintain them while the case is active:

| User-facing label | Proposed API/database field | Meaning |
| --- | --- | --- |
| Desired outcome | `desired_outcome` | The intended result, e.g. "Receive payment of $5,000", "Sign the service agreement", "Obtain a reply". |
| Expected close date | `expected_close_date` | The calendar date when the user expects the case to reach a business conclusion. |

**Do not conflate with existing fields:**
- `title` — case label, not a structured goal;
- `note` — general context, not a structured goal;
- `next_action` — immediate next operator step;
- `due_at` — next follow-up/reminder scheduling timestamp;
- `status` — actual lifecycle status (`open`, `due_today`, `overdue`, `done`, `lost`, `archived`);
- `completed_at` — actual completion time;
- `done_reason` / `lost_reason` — factual explanation when the user closes the case.

Example:
- **Desired outcome:** "Sign contract worth $5,000".
- **Expected close date:** "2026-11-30".
- **Next action:** "Call client to discuss final terms".
- **Next follow-up due:** "2026-10-16 10:00" (timestamp used for reminders).
- **Actual closure:** may occur before, on or after the expected close date, and must be recorded separately.

## 2. Proposed implementation contract

Field names and independent semantics above are approved for implementation. Compatibility defaults here are the planned design, not evidence of existing functionality.

- Both fields are **optional** so quick capture and existing saved cases remain valid.
- `desired_outcome` is nullable Unicode text, with a proposed 1,000-character API limit; empty or whitespace-only input is treated as not provided.
- `expected_close_date` is a nullable **calendar date**, transferred as ISO `YYYY-MM-DD`; not a timestamp and has no time-of-day/timezone offset.
- Date may be in the past (e.g. an overdue business target); closure is not automatically constrained by it.
- Values may be supplied on create, edited and explicitly cleared on active cases. In PATCH, an omitted field means *leave unchanged*; `null` means *clear*.
- Values remain persisted when an item is marked `done` or `lost`, reopened or archived. Existing mutation rules for terminal cases remain unchanged.
- Neither setting nor changing either field automatically schedules/cancels/reschedules reminders or mutates an existing lifecycle, date or payment property.
- Legacy API clients omitting both fields continue to work.

## 3. Required implementation surfaces

1. **Storage/domain:** new nullable `followup_items.desired_outcome` (`TEXT`) and `followup_items.expected_close_date` (`DATE`) via additive Alembic migration; update SQLAlchemy model and domain persistence flows.
2. **API contracts:** extend create, update, detail/list, board/registry schemas; validate text/date consistently; round-trip both values. Preserve owner checks and lifecycle invariants.
3. **Web UI:** two labelled fields in **Create follow-up**, editing on active **Item detail**, display desired outcome and expected close date alongside (not instead of) actual lifecycle details, and clear empty-value presentation.
4. **Verification:** test migration of existing PostgreSQL rows, API create/update/clear/read, validation, serialization, UI display, ownership, close/reopen persistence, and reminder/state non-interference; add manual acceptance checks when delivered.

The current Chrome extension only captures the active tab's title/URL and is **not** a full case-creation client. Do not declare extension create-form changes completed without creating a corresponding feature.

## 4. Acceptance criteria — all PENDING

- [ ] Create a case with both fields; retrieve them unchanged.
- [ ] Create a case without either; existing behaviour is unchanged.
- [ ] Update and clear each target field independently.
- [ ] Distinguish expected close date from next reminder due date in labels and persisted values.
- [ ] Reject invalid date formats; serialize valid dates consistently.
- [ ] Closing/reopening preserves targets and status/reminder/payment/reason invariants.
- [ ] Passing expected close date does not trigger auto-closure or additional reminders.
- [ ] Existing PostgreSQL data survives migration without invented targets.
- [ ] Web create/edit/detail surfaces show both fields.
- [ ] Implementation, tests and authoritative current-state docs agree.

## 5. Not part of this change

No automatic "goal achieved" evaluation, automatic closure, deadline escalation, extra notifications, CRM pipeline, task-management workflow engine or new billing behaviour.

**Do not change this document's status to implemented until code, migration and verification evidence exist.**
