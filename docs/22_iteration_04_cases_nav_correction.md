# Iteration 04 correction — Cases navigation wiring

## Problem
The initial Iteration 04 snapshot included `renderCases(...)` and the backend registry endpoint, but the main router and shell navigation did not expose the `#/cases` route.

## Fix
This correction wires:
- `#/cases` into the main `render()` dispatcher
- a `Cases` button into the shell header
- active-state styling for `Dashboard` and `Cases` navigation

## Expected result
A signed-in user can open the case registry from the top navigation and switch between `Dashboard` and `Cases` without manual URL editing.
