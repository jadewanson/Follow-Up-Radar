# 05. Domain Model

- **Owner role:** Architect
- **Тип истины:** предметная модель
- **Gate:** G3 / G4 / G5

## 1. Core entities

### User
Represents the single account owner.

Required fields:
- id
- email
- timezone
- plan
- plan_status
- created_at

### MagicLinkToken
Represents one pending sign-in challenge.

Required fields:
- id
- email
- token_hash
- expires_at
- consumed_at
- created_at

### UserSession
Represents one authoritative authenticated session.

Required fields:
- id
- user_id
- token_hash
- expires_at
- revoked_at
- created_at
- last_seen_at

### FollowUpItem
Represents one client or money follow-up obligation.

Required fields:
- id
- user_id
- title
- client_name
- item_type
- source_url
- note
- amount
- currency
- due_at
- status
- created_at
- updated_at
- completed_at
- archived_at

### Reminder
Represents one scheduled reminder for an item.

Required fields:
- id
- item_id
- user_id
- reminder_at
- status
- sent_at
- clicked_at
- canceled_at
- created_at

### Subscription
Reserved for billing ownership in later iterations.

Required fields:
- id
- user_id
- provider
- external_customer_id
- external_subscription_id
- plan
- status
- started_at
- renews_at
- canceled_at

### EventLog
Represents the immutable record of critical domain facts.

Required fields:
- id
- user_id
- event_type
- entity_type
- entity_id
- payload_json
- created_at
