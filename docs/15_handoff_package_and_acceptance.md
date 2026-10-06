# 15. Handoff Package and Acceptance

- **Owner role:** Delivery Manager + Architect
- **Тип истины:** transfer completeness
- **Gate:** G14

## 1. Handoff principle
The product is not “delivered” until another competent team can:
- understand it;
- run it;
- inspect it;
- support it;
- extend it without tribal knowledge.

## 2. Mandatory handoff contents
### Product pack
- Product Constitution
- Scope and non-goals
- User flows
- Success metrics
- Acceptance criteria

### Engineering pack
- Engineering Constitution
- Architecture/module ownership
- Domain model
- State machine
- API contracts
- DB schema/migrations
- Review law
- Testing strategy

### Delivery/ops pack
- deployment guide
- runbook
- rollback guide
- health checks
- config reference
- incident classes
- known limitations

### Code pack
- repository
- lockfiles
- migration files
- env example
- compose/infra manifests

### Quality pack
- smoke checklist
- latest test results
- release notes
- open issues register

## 3. Acceptance conditions
Handoff accepted only if:
- documents are complete and current;
- setup works from scratch;
- core loop works;
- runbook is usable;
- no hidden setup knowledge required.

## 4. Rejection conditions
Handoff rejected if:
- docs and code diverge materially;
- environment cannot be recreated;
- support procedures are undocumented;
- architecture truth depends on oral explanation.
