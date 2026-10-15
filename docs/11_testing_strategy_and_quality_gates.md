# 11. Testing Strategy and Quality Gates

- **Owner role:** QA Lead + Tech Lead
- **Type of truth:** quality proof
- **Gate:** G10 / release

## 1. Test philosophy
Tests exist to prove invariant preservation, not to inflate coverage metrics.

## 2. Required test layers
### Unit tests
Must cover:
- validators;
- config parser;
- state transitions;
- service-layer domain rules;
- idempotency guards.

### Integration tests
Must cover:
- auth flow;
- item CRUD;
- ownership checks;
- reminder scheduling;
- reminder dispatch;
- billing webhook verification.

### End-to-end smoke tests
Must cover:
- signup/login;
- create item;
- reminder sent;
- user returns;
- item closed.

## 3. Critical invariants to test
- no forbidden state transition;
- no cross-user item access;
- no duplicate reminder send;
- no item created without valid due state;
- no invalid config startup;
- no unauthenticated mutation.

## 4. Quality gates
### Gate Q1
No merge without unit tests for new domain logic.

### Gate Q2
No beta without integration tests on critical paths.

### Gate Q3
No launch without smoke suite pass on release candidate.

## 5. Known-issue policy
Known P0 or P1 core-loop bug blocks beta/launch.
Known cosmetic issue can be tolerated if documented.

## 6. Manual testing
Manual testing supplements, but never replaces:
- state-machine proof;
- ownership proof;
- reminder reliability proof.

## 7. Acceptance checklist
A release candidate is acceptable only if:
- user can create item;
- reminder is reliably scheduled;
- reminder is delivered;
- user can return and close;
- observability exists for failures.
