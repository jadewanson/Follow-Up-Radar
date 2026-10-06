# Web interface

The static browser client for the iteration 14 development snapshot. It covers sign-in by magic link, case capture and review, filters and follow-up actions, activation, beta interest, and internal beta billing controls. Domain state remains in the backend.

## Start

From `web/`, run `npm ci && npm run dev`, then open `http://localhost:5173`. The API must be running at `http://localhost:8000`; follow the root README for database, Redis, and backend setup.

The development server serves files from `web/` and falls back to `index.html` for app routes. It is intended for local use only. There is no production build pipeline or configured frontend lint task yet.
