# Iteration 02 runbook

## Backend environment
Copy `.env.example` to `.env` and set:
- `APP_SECRET_KEY`
- `APP_BASE_URL`
- `DEV_EMAIL_OUTBOX_PATH`

## Migrations
Run Alembic upgrade to include iteration 02 schema.

## Jobs
Run reminder dispatch:

```bash
python -m app.jobs.reminder_dispatch_job
```

Run daily digest:

```bash
python -m app.jobs.daily_digest_job
```

## Web
From `web/`:

```bash
npm run dev
```

Open `http://localhost:5173`.
The web app talks to `http://localhost:8000` by default.

## Development sign-in
Request a magic link in the web UI.
The delivered message is written to `DEV_EMAIL_OUTBOX_PATH`.
Open the URL from the outbox file or paste the token manually into the verify form.
