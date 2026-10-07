# Web interface

The static browser client for the iteration 14 development snapshot. It covers sign-in by magic link, case capture and review, filters and follow-up actions, activation, beta interest, and internal beta billing controls. Domain state remains in the backend.

## Start

For the complete stack, follow the root README and run `docker compose up -d --build` from the repository root. Then open `http://localhost:5173`.

To run only the web client on the host, from `web/` run `npm ci && npm run dev`. The API must already be running at `http://localhost:8000`.

The development server serves files from `web/` and falls back to `index.html` for app routes. It is intended for local use only. There is no production build pipeline or configured frontend lint task yet.
