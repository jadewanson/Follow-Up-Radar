# Iteration 06 — Scheduled naming + state visibility hardening

## Scope
- Rename Dashboard third section from `Upcoming` to `Scheduled`.
- Harden item detail as the authoritative state surface.
- Keep the product inside the follow-up control-layer design.

## Changes
- Board response and UI now use `scheduled`.
- Item detail now shows a dedicated state block with:
  - lifecycle badge
  - payment marker
  - last case status change
  - last payment update
- Activity is now grouped into:
  - `State changes`
  - `Operational activity`
- Event summaries now use clearer case-oriented wording.

## Non-goals
- No CRM entities
- No workflow engine
- No global audit center
- No new domain axes beyond lifecycle and payment state
