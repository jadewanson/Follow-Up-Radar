# 14. Launch Readiness and Beta Protocol

- **Owner role:** Product Owner + Delivery + SRE
- **Type of truth:** launch discipline
- **Gate:** G11 / G12 / G13

## 1. Beta goal
Validate that real users:
- create items;
- receive reminders;
- return;
- close outcomes;
- understand value.

## 2. Beta cohort
- narrow ICP only;
- 5–10 users to start;
- manual onboarding allowed.

## 3. Beta success criteria
- users can complete activation path;
- reminder return is observed;
- no core data loss;
- no persistent duplicate sends;
- product is described by users in money/follow-up terms.

## 4. Beta anti-goals
Do not use beta to:
- open new scope categories;
- test every future idea;
- validate CRM demand;
- validate inbox sync demand.

## 5. Launch readiness checklist
Before public launch:
- PRR passed;
- smoke tests passed;
- support email exists;
- privacy policy exists;
- extension permissions are minimal and explained;
- billing and cancellation flow are clear;
- known limitations documented.

## 6. Hold conditions
Launch is blocked if:
- reminder reliability is uncertain;
- ownership isolation is broken;
- state machine bugs exist;
- invalid config can partially start service;
- users cannot recover from normal errors.

## 7. Post-launch review
After launch:
- inspect product metrics daily;
- inspect operational metrics daily;
- document incidents;
- no feature expansion until core loop proof is stable.
