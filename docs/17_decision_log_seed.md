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

## Template for future entries
### ADR-XXX — Title
- **Decision:**
- **Status:** proposed / accepted / rejected / superseded
- **Reason:**
- **Alternatives considered:**
- **Impact:**
- **Migration / rollback note:**
