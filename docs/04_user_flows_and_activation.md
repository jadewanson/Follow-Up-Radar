# 04. User Flows and Activation

- **Owner role:** Product Owner + UX owner
- **Тип истины:** пользовательские потоки
- **Gate:** G0 / G3 / G7 / G12

## 1. Primary flow
### Flow A — invoice/proposal follow-up
1. User installs extension or logs into web app.
2. User creates follow-up item.
3. User sets:
   - type;
   - due date;
   - client;
   - note;
   - optional amount.
4. System persists item.
5. System schedules reminder.
6. At due time system sends reminder.
7. User clicks reminder/open dashboard.
8. User acts:
   - sends follow-up outside the system;
   - reschedules;
   - closes as paid/done/lost.

## 2. Flow B — promised reply
1. User promises a reply.
2. User creates item quickly.
3. User gets due reminder.
4. User returns and closes outcome.

## 3. Activation path
Activation is:
- signup complete;
- first item saved;
- first reminder sent;
- first reminder-driven return.

## 4. UX commandment
Every screen must make the next right action obvious:
- create;
- reschedule;
- close;
- review overdue.

## 5. UX anti-patterns
Forbidden:
- dashboard as information wallpaper;
- multiple competing entry points;
- hidden status changes;
- overloaded forms;
- generic productivity language.

## 6. Required screens
- extension popup;
- web dashboard;
- item detail;
- settings/billing.

## 7. Empty states
Required empty states:
- no items;
- no overdue items;
- no reminders yet;
- free plan limit reached.

## 8. Error states
Required error states:
- item creation failed;
- reminder scheduling failed;
- auth expired;
- billing access blocked;
- service unavailable.

## 9. UX acceptance
A new user must be able to:
- understand product in under 30 seconds;
- create first item in under 2–3 minutes;
- understand what happens next without documentation.
