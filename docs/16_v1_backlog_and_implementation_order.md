# 16. v1 Backlog and Implementation Order

- **Owner role:** Delivery + Tech Lead
- **Тип истины:** execution backlog
- **Gate:** execution planning

## 1. Sequence law
Implementation order is not optional.

## 2. Build order
### Block A — foundation
1. repo skeleton
2. config loader
3. DB session
4. migrations
5. health endpoints

### Block B — auth
6. magic-link request
7. token verify
8. current user dependency

### Block C — domain core
9. item schema/model
10. item create/read/update
11. ownership checks
12. status service
13. reschedule/complete actions
14. event logging

### Block D — reminder core
15. reminder model
16. schedule on create
17. worker/queue
18. dispatch job
19. idempotency guard
20. send status handling

### Block E — web surface
21. dashboard
22. item detail
23. create/edit form
24. status actions
25. settings

### Block F — extension
26. manifest v3
27. popup
28. tab title/url capture
29. quick create
30. open dashboard

### Block G — billing
31. checkout
32. webhook verification
33. plan gating
34. billing page

### Block H — hardening
35. daily digest
36. filters
37. smoke suite
38. PRR package
39. beta package
40. handoff package

## 3. Priority rules
- P0 before P1
- reliability before polish
- observability before scale
- proof before expansion

## 4. Forbidden backlog pollution
Do not add:
- mobile;
- AI;
- inbox sync;
- CRM features;
- team management;
- generic automation.

## 5. Completion condition
v1 is complete when the authoritative core loop works, not when the backlog is aesthetically “full”.

## 6. Approved product addition after iteration 14 — TO IMPLEMENT

**Case desired outcome and expected close date** are approved, but absent from the current snapshot. [Issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) tracks implementation of the case create/edit surfaces, persisted fields, API contracts, migration and tests. Do not mark implemented before code and verification evidence exist.

Specification: [`34_planned_case_desired_outcome_and_expected_close_date.md`](34_planned_case_desired_outcome_and_expected_close_date.md). This addition does not supersede historical build order above.
