# 06. State Machine

- **Owner role:** Architect + Tech Lead
- **Тип истины:** authoritative state behavior
- **Gate:** G3 / G5 / G10

## 1. Allowed item statuses
Only:
- open
- due_today
- overdue
- done
- paid
- lost
- archived

## 2. Semantics
- **open:** valid active item not yet due.
- **due_today:** active item that reached current due day.
- **overdue:** active item past due.
- **done:** terminal non-money success.
- **paid:** terminal money-success outcome.
- **lost:** terminal unsuccessful outcome.
- **archived:** hidden/inactive after closure or explicit archival.

## 3. Allowed transitions
- open → due_today
- due_today → overdue
- open → done
- open → paid
- open → lost
- due_today → done
- due_today → paid
- due_today → lost
- overdue → done
- overdue → paid
- overdue → lost
- done → archived
- paid → archived
- lost → archived

## 4. Reschedule rule
Reschedule does not create a new semantic status.
Reschedule updates due_at and may move:
- overdue → open (if future due date)
- due_today → open (if moved out of today)

This transition must be explicit and logged.

## 5. Forbidden transitions
Examples:
- paid → open
- lost → open
- archived → open
- done → paid
- paid → lost

Forbidden transitions return explicit error.

## 6. State authority
Status can be changed only by backend service layer.
Frontend never infers or forces terminal state.

## 7. Test requirements
Every allowed transition:
- positive test
Every forbidden transition:
- negative test
