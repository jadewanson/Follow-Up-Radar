# Follow-Up Radar — Iteration 01 Apply Notes

This repository snapshot already includes iteration 01 and its corrections.

## What changed in the corrected baseline
- fixed auth timezone handling
- removed read-side hidden database writes from item GET/list paths
- collapsed migrations to one authoritative path under `backend/alembic/versions/`
- unified health/system routing ownership
- cleaned duplicate documentation files

## Migration authority
Use only Alembic migrations under:
- `backend/alembic/versions/`

Do not execute any second migration path.

## Verification steps
1. Configure `.env`
2. Run Alembic migrations
3. Start backend
4. Run tests
5. Verify `/health/live`

## Scope reminder
Current scope still excludes:
- reminder email dispatch
- daily digest
- billing
- extension-driven capture workflows beyond scaffold level
