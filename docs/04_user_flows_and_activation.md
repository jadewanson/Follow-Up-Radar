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

## 10. Approved future flow extension — not yet implemented

When creating a case in the web app, the user may additionally enter:
- **Desired outcome:** what business result they intend to achieve.
- **Expected close date:** the calendar day by which they hope to resolve the case.

On an active case, the user can review and update these values. Item detail distinguishes **next action**, **next follow-up/reminder due date**, **expected close date**, and **actual completion**. A closing action still records `done` or `lost` with an actual outcome reason; the target does not automatically determine closure.

These fields are **planned, not available in the current UI**. See [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) and [specification](34_planned_case_desired_outcome_and_expected_close_date.md).

## 11. Future closure UX — compare expectation with actual result (not implemented)

When closing a case **with a saved desired outcome**, the dialog presents the desired outcome, required actual outcome reason, and a **single-choice** assessment: Exceeded expectations / Met expectations / Below expectations. It may be left unanswered; the existing `done`/`lost` transition still requires an actual reason. Without a desired outcome no comparison is requested. No automatic comparison is performed. See [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6) and [specification](34_planned_case_desired_outcome_and_expected_close_date.md).
