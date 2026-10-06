# Iteration 04 — Case Registry & Lifecycle View

## Goal
Add a dedicated Cases view that shows all follow-up items for the current user, with scope filters and a short lifecycle summary per case.

## What changed
- Added `GET /items/registry?scope=all|active|closed`
- Added backend registry read model with `last_event_at` and `last_event_summary`
- Added `#/cases` in web UI
- Added scope buttons: All / Active / Closed
- Added registry rows with current status, due date, amount, created timestamp, last activity and `Open` action

## Constraints
- No new domain entity was introduced
- Full activity remains on item detail
- Dashboard remains the operational active board
- Cases is a registry and navigation surface, not a CRM workspace

## Manual smoke
1. Sign in
2. Create one active item and one closed item
3. Open `#/cases`
4. Confirm `All / Active / Closed` filters work
5. Confirm each row shows lifecycle summary
6. Confirm `Open` routes to item detail with full Activity section
