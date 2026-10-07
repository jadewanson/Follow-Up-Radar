# 13. Deployment Runbook and Operations

- **Owner role:** DevOps/SRE
- **Type of truth:** operational truth
- **Gate:** G11 / G13 / G14

## 1. Deployment principles
- deployment must be repeatable;
- migrations are explicit;
- startup fails on invalid config;
- health checks exist before accepting traffic;
- secrets are injected by the deployment environment, never committed.

## 2. Current operational surfaces
- liveness endpoint;
- readiness endpoint;
- structured application logs;
- durable reminder/digest delivery status in PostgreSQL;
- development file outbox or real SMTP email transport.

A separately scheduled worker/queue and payment webhooks are not part of the current implementation and must not be assumed by operations.

## 3. Email delivery modes

### Development file outbox
Use:
- `EMAIL_DELIVERY_MODE=dev_file`
- `DEV_EMAIL_OUTBOX_PATH=<gitignored local path>`
- `EMAIL_FROM_ADDRESS=<development sender>`

No network email is sent.

### SMTP
Use:
- `EMAIL_DELIVERY_MODE=smtp`
- `EMAIL_FROM_ADDRESS=<verified sender>`
- `SMTP_HOST=<relay host>`
- `SMTP_PORT=<relay port>`
- `SMTP_SECURITY=starttls|ssl|none`
- `SMTP_USERNAME` and `SMTP_PASSWORD` together when authentication is required
- `SMTP_TIMEOUT_SECONDS=<positive seconds>`

`starttls` is the default. Port 465 is the default when `SMTP_SECURITY=ssl`; otherwise port 587 is the default. Unencrypted SMTP is rejected in staging and production.

The sender address/domain must satisfy the selected SMTP provider's verification and DNS requirements. Those provider-side settings are operational dependencies, not repository secrets.

## 4. Email security invariant

Magic-link tokens are persisted only as keyed hashes in `magic_link_tokens`. The raw one-time URL/token is passed directly to the email gateway and must not be stored in `notification_deliveries.body_text`, event payloads, logs, or source control. The delivery row stores a redacted audit marker instead.

Development file outbox messages do contain the raw token because that file is the local substitute for the recipient mailbox. The outbox path must remain local, gitignored, and inaccessible to untrusted users.

## 5. Startup sequence
1. validate config;
2. connect to PostgreSQL;
3. apply/verify migrations;
4. connect to Redis;
5. if SMTP is enabled, verify deployment secrets and relay reachability;
6. start API;
7. start the externally configured reminder/digest scheduler when one is deployed;
8. verify readiness;
9. send a controlled test message through the configured email mode before opening traffic.

## 6. Shutdown sequence
- stop accepting new work;
- stop external schedulers before application shutdown;
- finish or safely mark in-flight jobs;
- close DB/Redis connections;
- preserve logs and delivery failure surfaces.

## 7. Incident classes

### Class A
Auth failure, magic-link delivery failure, or user access corruption.

### Class B
Item write/read corruption.

### Class C
Reminder/digest scheduling or transport failure.

### Class D
Internal beta billing-state error.

## 8. Runbook minimum contents
- how to start and stop the system;
- how to verify health;
- how to inspect failed notification deliveries and reminders;
- how to retry non-sensitive transport failures safely;
- how to test SMTP without exposing credentials or magic-link tokens;
- how to rollback a release;
- how to recover from misconfiguration.

A failed magic-link send is not retried from the persisted delivery body because the secret is deliberately not persisted. The user requests a new link instead.

## 9. Backup/restore principles
- DB backups must be real, not assumed;
- restore process must be documented and testable;
- reminder duplication risk must be considered after restore;
- backups must not create a second source from which live magic-link secrets can be recovered.

## 10. Secrets/config rules
- secrets never hardcoded;
- `.env.example` contains only non-secret shape/placeholders;
- production SMTP password is stored in the deployment secret store;
- secrets rotation procedure is documented;
- logs and exception responses never contain SMTP credentials.

## 11. Operational anti-patterns
Forbidden:
- hand-run SQL fixes without log;
- hidden cron jobs outside runbook;
- undocumented environment variables;
- production-only logic branches that do not exist in docs;
- plaintext magic-link secrets in database rows or application logs;
- unencrypted SMTP in staging or production.
