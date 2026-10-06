# 07. Data Model and DB Schema

- **Owner role:** Architect + DB owner
- **Тип истины:** storage truth
- **Gate:** G4 / G5

## 1. Storage principles
- PostgreSQL is the only authoritative database.
- Schema changes only via Alembic migrations.
- Constraints are preferred over convention.
- Nullability must be deliberate.
- Allowed values must be centralized in contracts and mirrored in validation.

## 2. Required tables
- users
- magic_link_tokens
- user_sessions
- followup_items
- reminders
- subscriptions
- event_logs

## 3. Required indexes
### users
- unique(email)

### magic_link_tokens
- index(email)
- unique(token_hash)

### user_sessions
- index(user_id)
- unique(token_hash)

### followup_items
- index(user_id)
- index(due_at)
- index(status)
- index(type)

### reminders
- index(item_id)
- index(user_id)
- index(reminder_at)
- index(status)

### subscriptions
- index(user_id)

### event_logs
- index(user_id)
- index(event_type)
- index(created_at)
