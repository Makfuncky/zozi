# Seed Data — Architecture

## Production Seed (canonical — REQUIRED)

The canonical, production seed path inserts directly into the Neon PostgreSQL
tables via SQLAlchemy ORM, defined in:

  - `infrastructure/database/seed/_seed_constants.py` — all seed data as Python literals (single source of truth)
  - `infrastructure/database/seed/_common.py` — `seed_data()` function (uses the constants and inserts via SQLAlchemy)
  - `infrastructure/database/seed/seed_part{1,2,3}.py` — domain-specific seed helpers (re-exports)
  - `infrastructure/database/seed/__init__.py` — public re-exports

These are invoked by:
  - Application bootstrap (`_ensure_demo_user`, `bootstrap_default_accounts`)
  - `pytest` test fixtures (conftest's `db_session` runs `seed_data` if the DB is empty)
  - CI `alembic upgrade head` followed by `python -m scripts.run_seed`

Per **ADR-024 / upgrade_plan.md (Phase 1)**, all production seed data MUST
be inserted directly into the database tables from the Python module
`infrastructure.database.seed._seed_constants`.

## Legacy Dev Loader (deprecated — DO NOT USE)

`scripts/seed_loader.py` was a dev-only offline SQLite utility that previously
read JSON files from this directory. As of the 2026-09-07 seed migration,
it now reads from the canonical Python module (with a JSON fallback for
backward compat). The JSON files have been **removed** — production seed
data lives in Neon via the canonical module.
