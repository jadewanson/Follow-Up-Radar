# 08. API Contracts

- **Owner role:** Architect + API owner
- **Type of truth:** current service interface
- **Gate:** G4 / G5 / G9

## 1. Contract rules

- Inputs and outputs are typed.
- Domain failures use explicit structured errors.
- Authenticated ownership is enforced server-side.
- State mutation goes through backend services.
- Clients do not own lifecycle or payment state.
- The current API is a development/beta contract; billing endpoints mutate internal beta state and do not charge a card.

## 2. Auth

### POST /auth/request-magic-link
Input: email.  
Output: accepted status.

### POST /auth/verify
Input: email + token.  
Output: bearer access token + expiry.

### GET /auth/me
Authenticated current-user identity, timezone, plan, and plan status.

## 3. Cases

### POST /items
Creates a follow-up item and its initial reminder.

### GET /items
Lists owned cases. Supports lifecycle/type filters and archived inclusion.

### GET /items/board
Returns active cases grouped as overdue, due today, and scheduled.

### GET /items/registry
Returns the review registry with scope, search, sorting, lifecycle/payment/type/due/amount/review-signal filters.

### GET /items/{id}
Returns one owned case.

### GET /items/{id}/events
Returns activity belonging to that owned case.

### PATCH /items/{id}
Updates mutable case fields.

### POST /items/{id}/reschedule
Changes `due_at`, recomputes active lifecycle state, and maintains reminder coverage.

### POST /items/{id}/mark-paid
Changes payment state only.

### POST /items/{id}/complete
Closes an active case as `done` or `lost`; an outcome reason is required.

### POST /items/{id}/reopen
Reopens a `done` or `lost` case and re-arms reminder coverage.

### DELETE /items/{id}
Archives the owned case.

## 4. System/public surface

### GET /health/live
Process liveness only.

### GET /health/ready
Database + Redis readiness. External responses expose only stable reason codes, not raw infrastructure exception text.

### GET /v1/system/version
Development service version metadata.

### GET /v1/system/public-site-config
Public beta/pricing/support configuration.

### POST /v1/system/beta-interest
Stores a beta-interest request.

### GET /v1/system/activation-summary
Authenticated activation milestones.

### POST /v1/system/bootstrap-sample-case
Creates one sample case for the current user.

## 5. Billing beta surface

### GET /billing/summary
Returns current internal beta plan state.

### POST /billing/start-trial
Starts the internal Pro beta trial.

### POST /billing/upgrade
Moves the internal beta subscription to active Pro. This is not a real payment charge.

### POST /billing/cancel
Cancels the internal beta subscription with a required reason.

Real payment-provider checkout/webhook semantics are intentionally outside the current implemented contract and remain a separate backlog decision.
