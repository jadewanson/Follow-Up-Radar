# 17. Decision Log Seed

- **Owner role:** Product Owner + Architect
- **Type of truth:** change history
- **Gate:** all changes to constitutions/contracts

## Usage
Every material change to:
- scope;
- architecture;
- ownership;
- state machine;
- schema;
- API;
- launch gates

must be recorded here.

---

## ADR-001 — Narrow product scope
**Decision:** Product remains a follow-up control layer and does not expand into CRM/task-manager scope before paid validation.  
**Status:** accepted  
**Reason:** preserve product clarity and implementation quality.  
**Impact:** feature requests in adjacent categories are rejected.

## ADR-002 — Backend + PostgreSQL as SSOT
**Decision:** Domain truth resides only in backend + PostgreSQL.  
**Status:** accepted  
**Reason:** avoids split-brain state and hidden client truth.  
**Impact:** web and extension remain thin clients.

## ADR-003 — Fail-closed domain policy
**Decision:** Critical domain failures do not use best-effort continuation.  
**Status:** accepted  
**Reason:** predictable behavior and zero silent corruption.  
**Impact:** stricter error handling, more explicit failures.

## ADR-004 — Reminder engine is the product heart
**Decision:** reminder scheduling and delivery are treated as the central operational subsystem.  
**Status:** accepted  
**Reason:** without reminder-return-close the product has no differentiating value.  
**Impact:** reliability and idempotency work are P0.

## ADR-005 — Record intended case outcome and expected closure date
**Decision:** Add two user-entered case planning fields: `desired_outcome` and `expected_close_date`. Keep them independent of next-action reminders, actual completion, lifecycle and payment statuses.
**Status:** accepted product requirement; implementation pending ([issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6)).
**Reason:** The existing case captures the next contact but not explicitly the result the user aims to achieve or the anticipated case-end date.
**Alternatives considered:** store the goal in `note`/`title` and reuse `due_at` for the end date. Rejected because these have different meanings.
**Impact:** create/edit/detail UI, API create/update/read schemas, domain model, PostgreSQL migration, tests and docs. Existing records must remain valid.
**Migration / rollback note:** add nullable columns via additive Alembic migration; do not auto-populate business targets for old rows. Do not implement automatic closure or alter reminder scheduling.
**Scope:** [planned field specification](34_planned_case_desired_outcome_and_expected_close_date.md).

## Template for future entries
### ADR-XXX — Title
- **Decision:**
- **Status:** proposed / accepted / rejected / superseded
- **Reason:**
- **Alternatives considered:**
- **Impact:**
- **Migration / rollback note:**

### ADR-005 extension — subjectively compare expected and actual result (2026-10-12)
**Decision:** Add a planned optional `outcome_assessment` at explicit closure, selected as one of `exceeded`, `met`, `below`, or omitted (`null`). Display the saved desired outcome alongside the required actual closure reason. Preserve the comparison as separate from `done`/`lost`; never calculate it automatically. On reopen clear current assessment while retaining the closure event with a snapshot of the desired outcome.
**Status:** accepted product requirement, **implementation pending**, within [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6).
**Reason:** capture how well the case met its original business goal, not merely why the case was marked done or lost.
**Impact:** completion dialog, completion API, persisted case metadata, migration, event history and regression tests. See [planned specification](34_planned_case_desired_outcome_and_expected_close_date.md).
