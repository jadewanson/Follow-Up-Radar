# Iteration 02 — reminder dispatch, daily digest, web control surface

## Scope added
- reminder dispatch service
- notification delivery ledger
- daily digest service
- static web control surface
- board read model
- development email outbox delivery

## New authoritative components
- `notification_deliveries` table
- `NotificationDeliveryService`
- `ReminderDispatchService`
- `DailyDigestService`
- `GET /items/board`
- `web/` static control surface

## Rules
- backend remains the single source of truth
- web is still a thin control surface
- reminder dispatch is authoritative only after delivery state is persisted
- digest delivery is idempotent by day and user

## Remaining non-goals
- billing UI
- extension capture integration
- production SMTP provider
- analytics surface
