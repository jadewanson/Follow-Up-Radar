# Iteration 08 — Next Action + Outcome Reasons

## Goal
Make every open or closed case more explainable without leaving the target design.

## What changed
- Added `next_action` to follow-up items.
- Added `done_reason` and `lost_reason` to follow-up items.
- Added migration `0004_next_action`.
- Added item detail controls for:
  - saving `next_action`
  - entering an outcome reason when marking `done` or `lost`
- Added lifecycle-aware presentation in `Cases`:
  - active cases can show `next_action`
  - closed cases can show `done_reason` / `lost_reason`
- Added activity entries for `next_action` updates.

## Design boundary
This is not a workflow engine.
`next_action` is a short operator note explaining what should happen next.
`done_reason` and `lost_reason` explain why the case was closed.

## Acceptance
- A case can be created with an initial `next_action`.
- `next_action` can be updated from item detail.
- `done_reason` and `lost_reason` persist on close.
- Closing a case clears `next_action`.
- Item detail and Cases make these fields visible.
