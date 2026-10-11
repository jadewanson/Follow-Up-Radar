# 17. Decision Log Seed

- **Owner role:** Product Owner + Architect
- **Тип истины:** change history
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
