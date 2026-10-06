# 08. API Contracts

- **Owner role:** Architect + API owner
- **Тип истины:** service interface truth
- **Gate:** G4 / G5 / G9

## 1. Contract rules
- API must be versionable.
- Inputs and outputs must be typed.
- Errors must be explicit and structured.
- Every state mutation goes through API/service layer.
- No hidden side effects outside documented behavior.

## 2. Auth endpoints
### POST /auth/request-magic-link
Input:
- email

Output:
- status=accepted

### POST /auth/verify
Input:
- email
- token

Output:
- access_token
- token_type=bearer
- expires_at

### GET /auth/me
Output:
- user identity
- plan
- timezone
- account status

## 3. Item endpoints
### POST /items
Creates follow-up item and creates its reminder in the same authoritative flow.

### GET /items
Lists current user's items.

### GET /items/{id}
Returns one owned item.

### PATCH /items/{id}
Updates mutable fields only.

### POST /items/{id}/reschedule
Reschedules due_at and updates pending reminder.

### POST /items/{id}/complete
Transitions item to one terminal outcome.

### DELETE /items/{id}
Archives item.
