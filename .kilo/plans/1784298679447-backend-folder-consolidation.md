# Plan: Backend folder cleanup & consolidation (zero code loss)

**Date:** 2026-07-20 — **mode:** code (safe, move-only)
**Hard rule (per user):** NEVER delete source. Only `Move-Item`. Verify boot after
every batch. Nothing imported by `main.py` / app code gets moved.

---

## 0. Current state (verified by inspection)

Backend root has 150→41 files after prior pass. Remaining top-level dirs:

Wired into app (KEEP): `db/`, `models/`, `routers/`, `controllers/`, `services/`,
`utils/`, `providers/`, `middleware/` (6 modules used), `jobs/`, `data/`,
`location_service/`, `finance/`, `static/`, `uploads/`, `seeds/`, `log/`,
`tests/`, `alembic/`, `migrations/`, `accounts/` (uncertain — see §2).

Orphaned / not imported anywhere (MOVE to `archive/legacy/`): `api/`,
`dependencies/`, `tasks/`, `monitoring/`, `_recovered/`, `_trash/`.

Runtime artifacts in root: `zozi.db` (live) + many `zozi.db.*` backups.

`archive/` already exists and contains `trash/` (a pre-existing holding pen with
many duplicate source files — do NOT re-process; treat `archive/` as the
consolidation tomb).

---

## 1. Safety mechanism

- Snapshot current root + every dir listing to `C:\Users\user\AppData\Local\Temp\kilo\`
  before any move (rollback reference).
- Use `Move-Item -Force` only. No `Remove-Item` on any file/folder containing code.
- After each batch: `python -c "import main"` (route count must stay 1439) and
  `alembic heads` (must stay `0006`).
- `__pycache__/`, `.pytest_cache/`, `.venv/`, `venv/` are regenerable bytecode —
  LEFT untouched (zero risk, no code loss).

---

## 2. Classification & actions

### Batch A — Orphaned code dirs → `archive/legacy/` (preserved, recoverable)
Move whole directories (content intact):
- `api/` → `archive/legacy/api/`
- `dependencies/` → `archive/legacy/dependencies/`
- `tasks/` → `archive/legacy/tasks/`
- `monitoring/` → `archive/legacy/monitoring/`
- `_recovered/` → `archive/legacy/_recovered/`
- `_trash/` → `archive/legacy/_trash/`

> `accounts/` is NOT imported by `main.py` or any app module (verified). But it is
> a substantial accounting engine. Decision: MOVE to `archive/legacy/accounts/`
> too (preserves it, removes clutter). If later found needed, it is fully
> recoverable. (Flagged for user awareness.)

### Batch B — DB backups in root → `archive/db_backups/`
Move all `zozi.db.*` timestamped backups (keep live `zozi.db` in root):
- `zozi.db.bak`, `zozi.db.auditfix_*`, `zozi.db.bak_*`, `zozi.db.emptycc_*`,
  `zozi.db.idx_*`, `zozi.db.opendec_*` → `archive/db_backups/`
- Keep: `zozi.db`, `zozi.db-shm`, `zozi.db-wal` (live SQLite).

### Batch C — stray root source that is NOT app entry (already mostly moved)
Verify root only contains genuine app source + config + live db:
- Keep: `main.py`, `auth.py`, `config.py`, `models.py`, `schemas.py`,
  `database.py`, `database_logging.py`, `email_service.py`, `extract_schemas.py`,
  `fix_main.py`, `reconcile_db.py`, `run_server.py`, `start_server.py`,
  `run_location_server.py`, `security_verification.py`, `chat_system.py`,
  `README.md`, `.env`, `alembic.ini`, `pyproject.toml`, `requirements.txt`,
  `Dockerfile`, `__init__.py`, `perfume_bottle_100ml.png`, `tmp_apparel.png`,
  `zozi.db*`.
- If any leftover scratch `.py`/`.log`/`.out` remains → move to `log/` or `tests/`.

### Batch D — `archive/trash` cleanup (optional, low risk)
`archive/trash/` already holds duplicate source. Leave as-is (it is the existing
tomb). Do NOT delete. Only ensure no *live* file was accidentally placed there.

---

## 3. Final structure (target)

```
backend/
├── main.py auth.py config.py models.py schemas.py database*.py email_service.py
│   extract_schemas.py fix_main.py reconcile_db.py run_server.py start_server.py
│   run_location_server.py security_verification.py chat_system.py README.md
│   .env alembic.ini pyproject.toml requirements.txt Dockerfile __init__.py
│   zozi.db zozi.db-shm zozi.db-wal  perfume_bottle_100ml.png tmp_apparel.png
├── db/ models/ routers/ controllers/ services/ utils/ providers/
├── middleware/ jobs/ data/ location_service/ finance/ static/ uploads/
├── seeds/ log/ tests/ alembic/ migrations/
└── archive/
    ├── db_backups/   (zozi.db.* timestamped backups)
    ├── legacy/       (api/ dependencies/ tasks/ monitoring/ accounts/ _recovered/ _trash/)
    └── trash/        (pre-existing holding pen — untouched)
```

---

## 4. Validation after each batch
1. `python -c "import main; print(len(main.app.routes))"` → **1439**.
2. `alembic heads` → **0006_media_assets_cdn_url**.
3. `python -c "import providers, services, routers, controllers, models, db"` → OK.
4. No `FileNotFoundError` on boot (proves no wired module was moved).

## 5. Rollback
Every moved item's original path is recorded in the snapshot file. To undo any
batch: `Move-Item` back from `archive/legacy/<name>/` (or `archive/db_backups/`)
to its original location.
