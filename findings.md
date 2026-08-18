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

- `check_new_structure_compliance(repo, rep, eff)` defined at **line 14022**.
- Wired into `main()` at **line 14281** (after `check_subfolder_axis_and_shape`).
- NS codes present (full Seven-Laws coverage, NS0–NS22):
  - NS0 gate active; NS1–NS4 abolished root layers; NS5 required package missing;
    NS6 domain→module import; NS7 infra imported upward; NS8 cross-domain bypass;
    NS9 `_legacy` real logic; NS11 root `models/` canonical while domain models absent.
  - NS12 non-legacy files still import abolished flat layers (import debt); NS13
    `sys.path` injection of `_legacy` (false-GREEN cheat); NS14 new-axis adoption ratio.
  - NS15 require_feature() atom used but not registered in domains/*/features.py
    (Law 4 single-source); NS16 rbac aggregates split vs one domains/*/features.py;
    NS17 duplicate feature-atom keys across domains/*/features.py.
  - NS18 thin-router violation (router carries business logic, Law 2); NS19 module
    actor non-standard subpackage or direct `_legacy` import (Law 5 strangler);
    NS20 inverted arrows in middleware/providers/infrastructure (Law 1);
    NS21 missing country scope axis (axis 3); NS22 schema discipline
    (no __table_args__ schema='<domain>', Law 6).
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
| NS violations (from audit) | measured 2026-08-18 | 0 | running |
| **NS12** legacy import debt (non-legacy `from services./controllers./routers./models`) | **1787** | 0 | open (P0) |
| **NS13** `sys.path`→`_legacy` cheat | **2** (backend/main.py) | 0 | open (P0) |
| **NS14** new-axis adoption | 42% (new=1289, legacy=1787) | ~100% | open (YEL) |
| **NS15** feature atom not registered in domains/*/features.py | 0 | 0 | GREEN (Law 4) |
| **NS16** rbac aggregates split across sources | 0 | single source per domain | GREEN (Law 4) |
| **NS17** duplicate feature-atom keys | 0 | 0 | GREEN |
| **NS18** thin-router violation (router carries logic) | 238 | 0 | open (ADV, Law 2) |
| **NS19** module actor non-standard / direct _legacy import | 124 | 0 | open (ADV, Law 5) |
| **NS20** inverted arrows in middleware/providers/infra | 165 | 0 | open (P0, Law 1) |
| **NS21** missing country scope axis | 0 | axis present where needed | GREEN (axis 3) |
| **NS22** schema discipline (no __table_args__ schema) | 32 | 0 | open (ADV, Law 6) |
| NS1–NS4 abolished root-layer dirs | 0 at root (moved to `_legacy/`) | 0 | GREEN-by-cheat (now caught by NS12/13) |
