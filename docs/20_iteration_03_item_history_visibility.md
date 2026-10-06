# Iteration 03 — Item History Visibility

## Goal
Add a user-facing activity surface for a single follow-up item without expanding into a global audit center.

## Added
- backend endpoint `GET /items/{id}/events`
- backend event-to-summary mapping
- item detail `Activity` section in web UI
- backend test coverage for item event visibility and ownership

## Scope Rules
- item-only activity
- no auth history in main UI
- no raw payload JSON in frontend
- no global event explorer

## Acceptance
- existing item detail shows item history
- reminder and item events are visible in reverse chronological order
- foreign item history is not accessible
