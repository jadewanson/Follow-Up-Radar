# 13. Deployment Runbook and Operations

- **Owner role:** DevOps/SRE
- **Тип истины:** operational truth
- **Gate:** G11 / G13 / G14

## 1. Deployment principles
- deployment must be repeatable;
- migrations are explicit;
- startup fails on invalid config;
- health checks exist before accepting traffic.

## 2. Required operational surfaces
- liveness endpoint;
- readiness endpoint;
- structured logs;
- queue health visibility;
- failed reminder visibility;
- webhook failure visibility.

## 3. Startup sequence
1. validate config
2. connect to PostgreSQL
3. apply/verify migrations
4. connect to Redis
5. start API
6. start worker
7. verify readiness

## 4. Shutdown sequence
- stop accepting new work
- finish or safely mark in-flight jobs
- close DB/queue connections
- preserve logs and failure surface

## 5. Incident classes
### Class A
Auth failure or user access corruption

### Class B
Item write/read corruption

### Class C
Reminder queue/dead job issues

### Class D
Billing/webhook state errors

## 6. Runbook minimum contents
- how to start system;
- how to stop system;
- how to verify health;
- how to inspect failed reminders;
- how to retry transport failures safely;
- how to rollback release;
- how to recover from misconfiguration.

## 7. Backup/restore principles
- DB backups must be real, not assumed;
- restore process must be documented and testable;
- reminder duplication risk must be considered after restore.

## 8. Secrets/config rules
- secrets never hardcoded;
- .env.example contains only non-secret shape;
- secrets rotation procedure documented.

## 9. Operational anti-patterns
Forbidden:
- hand-run SQL fixes without log;
- hidden cron jobs outside runbook;
- undocumented environment variables;
- production-only logic branches that do not exist in docs.
