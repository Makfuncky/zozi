# Findings — ZOZI Backend Migration to NEW_STRUCTURE.md

> All numbers below are **measured on disk on 2026-08-18**, not assumed. The
> audit script (`scripts/system_trackers/system_architecture_audit.py`) is the
> automated tracker; these files are the manual tracker.

## 1 · The headline: the migration is COSMETIC, not real

`documents/NEW_STRUCTURE.md` defines a three-axis target (`modules/` = who,
`domains/` = what, `rbac/`+`domains/*/features.py` = may). The new folder
skeleton **exists**, but the running code does **not** use it.

| Evidence | Measured value | Meaning |
|---|---|---|
| `from services.` references in backend | **1745** | Code still imports the abolished `services` package |
| `from models` / `import models` (root flat) | **1676** | Code still imports the abolished root `models` package |
| `from controllers.` references | **474** | Code still imports the abolished `controllers` package |
| `from domains.` references | **380** | New packages are barely used by real code |
| `from modules.` references | 108 | New module layer barely wired |
| `from rbac.` references | 52 | RBAC not yet the gate everywhere |
| `from _legacy` references | **0** | Legacy code is NOT imported as `_legacy`; it re-exports under the OLD names via `sys.path`/shims, so `from services.` still "works" |

**Conclusion:** the 174 controllers / 196 services / 154 routers / 58 models /
67 utils / 13 db inside `backend/_legacy/` are the **real** code. The new
`domains/`+`modules/` packages are largely scaffold or regenerated stubs that
the app does not yet route through. This is exactly the "false migration" the
audit's NS gate was built to catch.

## 2 · Stale documentation vs reality (do NOT trust the doc's reality-check)

`documents/NEW_STRUCTURE.md` lines 794–811 contain a "Reality check" that
describes a **pre-migration** tree (flat `routers/` 223 files, `controllers/`
371, root `services/`, `models/` 27, etc.) and a 4-phase plan. **That state no
longer exists.** Verified current backend root dirs:

| Dir | Status | Files |
|---|---|---|
| `domains/` | EXISTS (target) | 1997 |
| `modules/` | EXISTS (target) | 701 |
| `rbac/` | EXISTS (target) | 106 |
| `kernel/` | EXISTS (target, refinement) | 10 |
| `infrastructure/` | EXISTS (target) | 230 |
| `_legacy/` | EXISTS (real code lives here) | 780 |
| `models/` | ROOT still canonical | 27 flat |
| `utils/` | ROOT still present | 67 flat |
| `db/` | ROOT still present | 12 flat |
| `providers/` | EXISTS | 90 |
| `events/`, `tasks/`, `tools/` | EXISTS (small) | 3 / 5 / 3 |
| `routers/` | **MISSING at root** | — |
| `controllers/` | **MISSING at root** | — |
| `services/` | **MISSING at root** | — |

## 3 · Audit script status (verified present on disk 2026-08-18)

`scripts/system_trackers/system_architecture_audit.py` (13,872 lines) already
enforces `NEW_STRUCTURE.md` via the anti-cheat gate:

- `check_new_structure_compliance(repo, rep, eff)` defined at **line 13793**.
- Wired into `main()` at **line 13970** (after `check_subfolder_axis_and_shape`).
- NS codes present: NS0 (gate active), NS1 (`controllers/` abolished), NS2
  (`routers/` abolished), NS3 (`services/` abolished), NS4 (`models/` abolished),
  NS5 (required package missing), NS6 (domain→module import), NS7
  (infra imported upward), NS8 (cross-domain bypass), NS9 (`_legacy` real logic),
  NS11 (root `models/` canonical while domain models absent).
- Docstring rewritten to cite `NEW_STRUCTURE.md` as authoritative.

This gate is the **tracking instrument** for the whole effort. It must stay the
single source of truth for "are we actually migrated?"

## 4 · RESOLVED — how legacy imports resolve (the crux)

**Confirmed 2026-08-18.** `backend/main.py` line 17:
`sys.path.append(os.path.join(_BACKEND_DIR, "_legacy"))`. This appends
`backend/_legacy/` to `sys.path`, so `_legacy/services`, `_legacy/controllers`,
`_legacy/models`, `_legacy/utils`, `_legacy/db`, `_legacy/routers` become
importable as top-level `services`, `controllers`, `models`, `utils`, `db`,
`routers`.

=> The 1745 `from services.` + 1676 `from models` + 474 `from controllers.`
references all resolve to `_legacy/` code. **The new `domains/`+`modules/`
packages are NOT what the app runs.** This `sys.path` trick is the entire
"migration" — removing it (Phase 6) will break boot unless the real code is
first relocated and rewritten. The import-rewrite strategy MUST run BEFORE
dropping `_legacy` from `sys.path`.

**Also found:** `domains/UNMAPPED/services` exists — a catch-all domain holding
not-yet-classified logic. Must be triaged in Phase 1 taxonomy reconciliation.

## 5 · Debt ledger (will be filled by audit + per-wave scans)

| Category | Baseline count | Target | Status |
|---|---|---|---|
| `from services.` | 1745 | 0 (→ `domains.<d>.services.`) | open |
| `from models` (root) | 1676 | 0 (→ `domains.<d>.models`) | open |
| `from controllers.` | 474 | 0 (→ `modules.<m>.routers` + `domains.<d>.services`) | open |
| `from domains.` (real adoption) | 380 | rising toward majority | open |
| `_legacy/` files | 780 | 0 | open |
| root `models/` `utils/` `db/` | 27 / 67 / 12 | 0 (moved) | open |
| NS violations (from audit) | TBD (audit running) | 0 | running |
