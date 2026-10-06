# Follow-Up Radar

Follow-Up Radar helps independent service providers and small studios keep track of client follow-ups: leads, proposals, invoices, and promised replies. Its core loop is **Capture → Schedule → Remind → Act → Close**. It is deliberately narrower than a CRM or general task manager.

## Status

This repository restores the **iteration 14 development snapshot**. It includes the API, a static web interface, a Chrome MV3 capture extension, migrations, tests, and product/engineering documentation. It is a development baseline, **not a production release**. Billing is an internal beta state flow; it does not charge cards or integrate a payment provider. End-to-end startup and database tests still need verification on a machine with Docker.

See [the restoration notes](docs/RESTORATION.md) for source and exclusions. The product scope and domain rules live in [the documentation index](docs/00_README.md).

Work is tracked in GitHub Issues; see [the issue workflow](docs/WORK_TRACKING.md).

## Repository map

| Path | Responsibility |
| --- | --- |
| `backend/` | FastAPI API, domain rules, PostgreSQL models and Alembic migrations, explicit reminder and digest jobs, tests |
| `web/` | Static browser interface served by a small Node development server |
| `extension/` | Chrome MV3 capture client |
| `docs/` | Product scope, contracts, architecture, runbooks, iteration notes |
| `infra/` | Infrastructure notes |
| `compose.yaml` | Local PostgreSQL and Redis |

The backend and PostgreSQL own domain state. The web app and extension are clients; neither is a source of truth. Email delivery defaults to a local file outbox during development and supports a real SMTP relay for deployed environments.

## Local setup

Prerequisites: **Python 3.13**, **Node.js**, and **Docker Compose**.

1. Copy `.env.example` to `.env` and set a local PostgreSQL password. Copy `backend/.env.example` to `backend/.env`. Set the same database password in `DATABASE_URL` and replace `APP_SECRET_KEY` with a newly generated local secret. Keep `APP_BASE_URL=http://localhost:5173`: magic links must open the web app, not the API. Both `.env` files are ignored by Git.
2. From the repository root, start the local services: `docker compose up -d postgres redis`.
3. In `backend/`, create and activate a virtual environment, install dependencies, load the environment, run migrations, and start the API:

   ```sh
   cd backend
   python3.13 -m venv .venv
   . .venv/bin/activate
   pip install -e '.[dev]'
   set -a; . ./.env; set +a
   alembic upgrade head
   uvicorn app.main:app --reload --port 8000
   ```

4. In another terminal, run `cd web && npm ci && npm run dev`; open `http://localhost:5173`.
5. Check `http://localhost:8000/health/live` and `http://localhost:8000/health/ready`. Development magic links are written to `var/dev_email_outbox`; open the link from that file or paste its token into the web app.

To run backend tests after setup: `cd backend && pytest`. The extension is loaded as an unpacked extension from `extension/` in Chrome; see its README for its limited role.

## Real email delivery

Set `EMAIL_DELIVERY_MODE=smtp` in `backend/.env` and provide an SMTP relay:

```dotenv
EMAIL_DELIVERY_MODE=smtp
EMAIL_FROM_ADDRESS=radar@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURITY=starttls
SMTP_USERNAME=replace-with-smtp-username
SMTP_PASSWORD=replace-with-smtp-password
SMTP_TIMEOUT_SECONDS=10
```

`SMTP_SECURITY` supports `starttls`, `ssl`, and `none`. Use `starttls` or `ssl` for deployed systems; unencrypted SMTP is rejected in staging and production. SMTP authentication is optional for relays that do not require it, but username and password must either both be present or both be absent.

The same delivery boundary sends sign-in magic links, reminders, and daily digests. One-time magic-link secrets are sent to the recipient but are not persisted in `notification_deliveries.body_text`; only a redacted audit marker is stored there.

## Safety and limitations

Never commit `.env` files, database data, dumps, mail outbox files, or generated caches. The tracked examples contain placeholders only. Production SMTP credentials belong only in deployment secrets. Before deploying, complete the operational checks in `docs/13_deployment_runbook_and_operations.md`.
