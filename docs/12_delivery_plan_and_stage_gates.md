# 12. Delivery Plan and Stage Gates

- **Owner role:** Delivery Manager
- **Type of truth:** execution sequence
- **Gate:** all

## 1. Phases
0. Product Constitution
1. Engineering Constitution
2. Environment & Repo Foundation
3. Domain Freeze
4. Data/API Contract Freeze
5. Backend Authoritative Core
6. Reminder Engine
7. Web Control Surface
8. Extension Capture Layer
9. Billing and Access Gates
10. Quality Hardening
11. Production Readiness Review
12. Controlled Beta
13. Production Launch
14. Handoff

## 2. Stage gates
### G0
Product Constitution approved.

### G1
Engineering Constitution approved.

### G2
Reproducible local environment works.

### G3
Domain model and state machine frozen.

### G4
DB schema and API contracts frozen.

### G5
Backend core works end-to-end without extension.

### G6
Reminder engine reliable and idempotent.

### G7
Web UI supports full core loop.

### G8
Extension acts as thin capture layer only.

### G9
Billing state is authoritative and verified.

### G10
Tests and quality hardening pass.

### G11
Production readiness review passes.

### G12
Controlled beta proves activation and return.

### G13
Production launch approved.

### G14
Handoff package complete.

## 3. Gate law
No team member may bypass a gate by:
- manual knowledge;
- hidden setup;
- “we’ll fix later” promises.

## 4. Escalation law
If a gate cannot be passed:
- stop;
- record blocker;
- fix blocker;
- do not open next phase.
