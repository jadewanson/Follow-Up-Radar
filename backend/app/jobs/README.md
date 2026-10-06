# Jobs

Iteration 02 introduces two authoritative job entrypoints:

- `python -m app.jobs.reminder_dispatch_job`
- `python -m app.jobs.daily_digest_job`

These jobs are intentionally explicit and synchronous at this stage.
The reminder engine and digest engine remain backend-owned, not web-owned.
