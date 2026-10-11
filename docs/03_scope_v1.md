# Scope v1

## P0
- create follow-up item
- due date
- dashboard list
- explicit statuses
- reminder scheduling
- reminder delivery
- reminder return path
- close or reschedule outcome
- event logging
- strict config and health endpoints

## Approved P0 addition (pending implementation, not in the current build)
- Record a free-text desired business outcome for each case.
- Record an expected calendar date for closing the case.
- Create and edit these independently of next follow-up/reminder due time and actual completion time.
- Persist and display both values without automatically changing lifecycle/payment/reminder behaviour.

Specification: [`34_planned_case_desired_outcome_and_expected_close_date.md`](34_planned_case_desired_outcome_and_expected_close_date.md). Tracking: [issue #6](https://github.com/jadewanson/Follow-Up-Radar/issues/6).

## P1
- filters
- daily digest
- follow-up message templates
- paywall and plan limit

## Forbidden before paid validation
- inbox sync
- AI suggestions
- mobile app
- teams
- deal pipelines
- accounting and contracts
