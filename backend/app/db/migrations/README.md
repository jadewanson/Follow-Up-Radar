# Migrations authority

Authoritative schema migrations live only under `backend/alembic/versions/`.

This directory is intentionally not used for executable migrations. It exists only to prevent drift back to a second migration path.
