# 09. Repository Structure and Module Ownership

- **Owner role:** Architect + Tech Lead
- **Type of truth:** codebase topology
- **Gate:** G2 / G4 / G5

## 1. Canonical repository layout
```text
followup-radar/
  backend/
  web/
  extension/
  infra/
  docs/
```

## 2. Backend structure
```text
backend/
  app/
    main.py
    config.py
    deps.py
    api/
    models/
    schemas/
    services/
    jobs/
    db/
  worker/
  tests/
```

## 3. Ownership map
### backend/app/config.py
Single owner of configuration parsing and validation.

### backend/app/services/item_service.py
Single owner of FollowUpItem domain mutations.

### backend/app/services/reminder_service.py
Single owner of reminder creation/scheduling semantics.

### backend/app/services/billing_service.py
Single owner of subscription state transitions from provider events.

### backend/app/services/event_service.py
Single owner of event logging semantics.

### backend/app/api/*
Thin transport layer only; no business truth.

### web/*
Presentation/control surface only.

### extension/*
Capture layer only.

## 4. Forbidden repository patterns
- duplicate service logic in api routes;
- business logic in frontend state stores;
- backend bypasses from extension;
- generic “utils” dumping ground;
- parallel alternate implementations of the same domain service.

## 5. Docs layout
Every major truth type gets its own file.
Do not merge all truth types into one giant mutable document.
