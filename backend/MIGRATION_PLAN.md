# ZOZI Backend — Migration Plan: Root Packages → New Structure

**Rule: no git operations. Boot must stay green after every step.**

## Current State (verified)
- App boots from root packages: `services/`, `controllers/`, `models/`, `db/`, `utils/`, `routers/`
- New-structure shells already exist but are mostly orphaned:
  - `domains/*/` — ~520 files across 13 domains, **not imported by the app**
  - `modules/*/routers/` — 175 relocated controllers, **not loaded by `main._load_routers()`**
  - `infrastructure/database/` — exact copy of `db/` (12 files)
  - `infrastructure/utils/` — exact copy of `utils/` (66 files)
  - `rbac/` — empty shell
  - `kernel/` — empty shell
- Import volume from root packages (regex scan, verified):
  - `services.` → **3 156 hits in 1 493 files**
  - `utils.` → **2 524 hits in 1 391 files**
  - `db.` → **1 477 hits in 1 179 files**
  - `controllers.` → **1 048 hits in 742 files**
  - `models.` → **585 hits in 257 files**
  - `routers.` → **409 hits in 399 files**
- Import volume from new packages:
  - `domains.` → 291 hits in 104 files (already partially active)
  - `infrastructure.` → 307 hits in 157 files (already partially active)
  - `rbac.` → 0 hits
  - `kernel.` → 17 hits in 17 files

## Migration Strategy

**Incremental, domain-by-domain, boot-after-each-domain.**

1. Pick one domain.
2. Move its services, models, and relocated controllers into the new tree.
3. AST-rewrite imports in every file that references the old paths.
4. Boot-test (`python -c "import main"`).
5. If green → remove the old root copies for that domain.
6. Repeat.

### Why this order
- **db/** and **utils/** are already copied to `infrastructure/`. They become Phase 0 once domain services no longer need them at root.
- **services/** is the heaviest dependency (1 493 importers). Migrating one domain at a time keeps the blast radius small.
- **controllers/** relocation is already 175/188 done; the remaining 13 are completed during their domain's migration.
- **routers/** is last because `main._load_routers()` currently globs `routers/**`; switching to `modules/**` is a single loader change after controllers are the active source.

---

## Table 1 — Services (`backend/services/` → `domains/{domain}/services/`)

| # | Source (`backend/services/...`) | Target (`domains/.../services/`) | Importers (est.) | Notes |
|---|---|---|---|---|
| 1 | `services/catalog/` | `domains/catalog/services/` | ~5 controllers | **1:1 clear mapping. 16 files. Pilot candidate.** |
| 2 | `services/comms/` | `domains/comms/services/` | ~10 controllers | 44 files; some overlap with `services/communication/` |
| 3 | `services/country/` | `domains/country/services/` | ~8 controllers | 35 files; merge with `services/geography/` |
| 4 | `services/customer/` | `domains/customers/services/` | ~3 controllers | 5 files; `domains/customers/services/` already has superset (12 files) |
| 5 | `services/finance/` | `domains/finance/services/` | ~20 controllers | 39 files; treasury slice stays here |
| 6 | `services/hr/` | `domains/hr/services/` | ~8 controllers | 32 files |
| 7 | `services/logistics/` | `domains/logistics/services/` | ~10 controllers | 26 files |
| 8 | `services/orders/` | `domains/orders/services/` | ~12 controllers | 18 files |
| 9 | `services/products/` | `domains/catalog/services/` | ~3 controllers | 2 files; products = catalog |
| 10 | `services/supplier/` + `services/suppliers/` | `domains/suppliers/services/` | ~10 controllers | 29 files total |
| 11 | `services/treasury/` | `domains/finance/treasury/` | ~8 controllers | 27 files; sub-slice of finance |
| 12 | `services/media/` | `domains/media/services/` | ~5 controllers | 0 files currently; shell only |
| 13 | `services/payments/` | `domains/payments/services/` | ~6 controllers | 0 files; shell only |
| 14 | `services/governance/` | `domains/governance/services/` | ~4 controllers | 3 files |
| 15 | `services/admin/` | `domains/governance/services/` | ~15 controllers | 46 files; admin ops = governance |
| 16 | `services/core/` | distributed to respective domains | ~40 controllers | 68 files; each file mapped to its owning domain by name/actor |
| 17 | `services/common/` | `infrastructure/utils/` or `domains/common/` | ~10 controllers | 23 files; shared helpers |
| 18 | `services/public/` | distributed to respective domains | ~10 controllers | 21 files |
| 19 | `services/security/` | `domains/governance/services/` or `infrastructure/security/` | ~6 controllers | 32 files |
| 20 | `services/identity/` | `domains/accounts/services/` | ~4 controllers | 2 files |
| 21 | `services/geography/` | `domains/country/services/` | ~5 controllers | 35 files; merge with `services/country/` |
| 22 | `services/hr/` | `domains/hr/services/` | ~8 controllers | 32 files |
| 23 | `services/analytics/` | `domains/governance/services/` | ~3 controllers | 3 files |
| 24 | `services/audit/` | `domains/governance/services/` | ~2 controllers | 6 files |
| 25 | `services/users/` | `domains/accounts/services/` | ~4 controllers | 7 files |
| 26 | `services/unknown/` | `domains/unknown/services/` | ~2 controllers | 1 file |
| 27 | `services/system/` | distributed | ~5 controllers | 4 files |
| 28 | `services/reviews/` | `domains/catalog/services/` | ~3 controllers | 0 files; shell only |
| 29 | `services/search/` | `domains/catalog/services/` or `infrastructure/search/` | ~3 controllers | 0 files; shell only |
| 30 | `services/uploads/` | `domains/media/services/` | ~2 controllers | 0 files; shell only |
| 31 | `services/ai/` | `domains/media/services/` | ~3 controllers | 15 files |
| 32 | `services/gateways/` | `domains/finance/services/` | ~4 controllers | 10 files |
| 33 | `services/location_service/` | `domains/country/services/` | ~2 controllers | 2 files |
| 34 | `services/documents/` | `domains/media/services/` | ~1 controller | 0 files; shell only |
| 35 | `services/mcp/` | `domains/media/services/` | ~1 controller | 1 file |
| 36 | `services/reporting/` | `domains/governance/services/` | ~2 controllers | 0 files; shell only |
| 37 | `services/configuration/` | `infrastructure/` | ~1 controller | 0 files; shell only |
| 38 | `services/api/` | `infrastructure/` | ~1 controller | 1 file |
| 39 | `services/communication/` | `domains/comms/services/` | ~1 controller | 1 file |
| 40 | `services/permissions/` | `domains/governance/services/` | ~2 controllers | 0 files; shell only |
| 41 | `services/customer/` | `domains/customers/services/` | ~3 controllers | 5 files (already counted in #4) |
| 42 | `services/employee/` | `domains/hr/services/` | ~2 controllers | 2 files |

**Services not listed above**: `services/employee/` (2 files, maps to domains/hr/), `services/customer/` (5 files, maps to domains/customers/).

**Total service files to migrate**: ~575 across 42 subdirs.

---

## Table 2 — Controllers (`backend/controllers/` → `modules/` / `rbac/` / `kernel/` / `infrastructure/` / `domains/`)

| # | Source (`backend/controllers/...`) | Target | Status |
|---|---|---|---|
| 1–42 | `controllers/admin/*` (42 files) | `modules/admin/routers/` | **42/42 relocated** |
| 43–45 | `controllers/catalog/*` (3 files) | `modules/catalog/routers/` | **3/3 relocated** |
| 46–53 | `controllers/commerce/*` (8 files) | `modules/commerce/routers/` | **8/8 relocated** |
| 54–58 | `controllers/comms/*` (5 files) | `modules/comms/routers/` | **5/5 relocated** |
| 59–124 | `controllers/core/*` (66 files) | `modules/core/routers/` | **66/66 relocated** |
| 125 | `controllers/customer/users.py` (1 file) | `modules/customer/routers/` | **1/1 relocated** |
| 126–130 | `controllers/finance/*` (5 files) | `modules/finance/routers/` | **5/5 relocated** |
| 131–136 | `controllers/hr/*` (6 files) | `modules/hr/routers/` | **6/6 relocated** |
| 137–142 | `controllers/logistics/*` (6 files) | `modules/logistics/routers/` | **6/6 relocated** |
| 143–147 | `controllers/orders/*` (5 files) | `modules/orders/routers/` | **5/5 relocated** |
| 148 | `controllers/products/*` (1 file) | `modules/products/routers/` | **1/1 relocated** |
| 149–164 | `controllers/public/*` (16 files) | `modules/public/routers/` | **16/16 relocated** |
| 165–171 | `controllers/supplier/*` (7 files) | `modules/supplier/routers/` | **7/7 relocated** |
| 172–174 | `controllers/treasury/*` (3 files) | `modules/treasury/routers/` | **3/3 relocated** |
| 175–177 | `controllers/unknown/*` (3 files) | `modules/unknown/routers/` | **3/3 relocated** |
| 178 | `controllers/identity/iam_controller.py` | `rbac/routers/` | **RELOCATE** |
| 179–181 | `controllers/security/*` (4 files) | `rbac/routers/` | **RELOCATE** |
| 182 | `controllers/users/workflow_controller.py` | `rbac/routers/` | **RELOCATE** |
| 183 | `controllers/governance/command_center_controller.py` | `domains/governance/routers/` | **RELOCATE** |
| 184 | `controllers/search/search_controller.py` | `infrastructure/search/routers/` | **RELOCATE** |
| 185–187 | `controllers/geography/*` (4 files) | `kernel/geography/routers/` | **RELOCATE** |
| 188 | `controllers/analytics/analytics_fallback_controller.py` | `modules/admin/routers/` | **RELOCATE** |
| 189 | `controllers/configuration/*` (0 controllers) | — | No controllers in this subdir |

**Remaining to relocate**: 13 controllers (identity, security, users, governance, search, geography, analytics_fallback).

**Delegators / bridges** (`controllers/delegators/` and `controllers/router_bridges/`): 150 files. These are NOT standard controllers. They must be classified:
- Thin delegators → move to `domains/{domain}/services/`
- Router bridges → move to `modules/{module}/routers/` or delete if obsolete

---

## Table 3 — Modules / Infrastructure / RBAC / Kernel

| # | Source | Target | Notes |
|---|---|---|---|
| 1 | `backend/db/` (10 files) | `infrastructure/database/` | **Already copied.** Rewire `from db.` → `from infrastructure.database.`, then remove root `db/`. |
| 2 | `backend/utils/` (66 files) | `infrastructure/utils/` | **Already copied.** Rewire `from utils.` → `from infrastructure.utils.`, then remove root `utils/`. |
| 3 | `backend/models/` (28 flat files + subdirs) | `domains/{domain}/models/` | Per-file mapping below. |
| 4 | `backend/routers/` (~200 files) | `modules/{module}/routers/` + regenerate | Hand-written routers split by actor; generated routers regenerated after controller retarget. |
| 5 | `backend/modules/*/routers/` (175 files) | Keep | Already relocated. Will become active source after `auto_router.py` retarget. |
| 6 | `backend/rbac/` | Keep and populate | Add `catalog.py`, `roles.py`, `resolution.py`, `dependencies.py`, `service.py`. |
| 7 | `backend/kernel/` | Keep and populate | Add `money.py`, `numbering.py`, `country.py`, `period.py`. |

### Models mapping (flat files → domains)

| Source file | Target domain | Target path |
|---|---|---|
| `models/admin.py` | governance | `domains/governance/models/admin.py` |
| `models/ai_upload.py` | media | `domains/media/models/ai_upload.py` |
| `models/commission.py` | finance | `domains/finance/models/commission.py` |
| `models/communication.py` | comms | `domains/comms/models/communication.py` |
| `models/core.py` | distributed | Cross-cutting; keep at root or split into respective domains |
| `models/countries.py` | country | `domains/country/models/countries.py` |
| `models/country_control.py` | country | `domains/country/models/country_control.py` |
| `models/country_enhancements.py` | country | `domains/country/models/country_enhancements.py` |
| `models/employee_models.py` | hr | `domains/hr/models/employee_models.py` |
| `models/erp.py` | finance | `domains/finance/models/erp.py` |
| `models/finance.py` | finance | `domains/finance/models/finance.py` |
| `models/fraud.py` | governance | `domains/governance/models/fraud.py` |
| `models/incident.py` | governance | `domains/governance/models/incident.py` |
| `models/logistics.py` | logistics | `domains/logistics/models/logistics.py` |
| `models/marketing.py` | catalog | `domains/catalog/models/marketing.py` |
| `models/media_models.py` | media | `domains/media/models/media_models.py` |
| `models/mixins.py` | infrastructure | `infrastructure/database/base.py` (merge) |
| `models/onboarding.py` | customers | `domains/customers/models/onboarding.py` |
| `models/orders.py` | orders | `domains/orders/models/orders.py` |
| `models/payments.py` | payments | `domains/payments/models/payments.py` |
| `models/permissions.py` | governance | `domains/governance/models/permissions.py` |
| `models/products.py` | catalog | `domains/catalog/models/products.py` |
| `models/promotions.py` | catalog | `domains/catalog/models/promotions.py` |
| `models/suppliers.py` | suppliers | `domains/suppliers/models/suppliers.py` |
| `models/upload_job.py` | media | `domains/media/models/upload_job.py` |
| `models/user.py` | customers | `domains/customers/models/user.py` |
| `models/__init__.py` | keep as root shim | Re-export from new locations for backward compat during transition |

### Models subdirs (already partially in domains/)

| Source | Target | Notes |
|---|---|---|
| `models/comms/*` (4 files) | `domains/comms/models/` | Already partially migrated |
| `models/core/` (1 file) | `domains/core/models/` or distribute | |
| `models/finance/` (1 file) | `domains/finance/models/` | Already partially migrated |
| `models/geography/*` (6 files) | `domains/country/models/` | Already partially migrated |
| `models/logistics/` (1 file) | `domains/logistics/models/` | Already partially migrated |
| `models/orders/` (1 file) | `domains/orders/models/` | Already partially migrated |
| `models/permissions/` (1 file) | `domains/governance/models/` | Already partially migrated |
| `models/supplier/` (1 file) | `domains/suppliers/models/` | Already partially migrated |

---

## Execution Order (safe increments)

### Phase 0 — Pre-flight (no file moves)
1. Run `python routers/generated/auto_router.py --verify` to establish router baseline.
2. Record current route count: `python -c "import main; print(len(main.app.routes))"`.
3. Build import map: scan every `.py` file for `from services.`, `from controllers.`, `from models.`, `from db.`, `from utils.`, `from routers.` and build a `{old_import: new_import}` lookup table per domain.

### Phase 1 — Infrastructure layer (db + utils)
**Risk: LOW. Already copied.**
1. Rewrite all `from db.` → `from infrastructure.database.` across the codebase.
2. Rewrite all `from utils.` → `from infrastructure.utils.` across the codebase.
3. Boot-test.
4. If green → remove root `db/` and `utils/`.

### Phase 2 — Pilot domain: `catalog`
**Risk: LOW. Small, 1:1 mapping, no cross-domain services.**
1. Move `services/catalog/` files into `domains/catalog/services/` (merge with existing 21 files).
2. Move `models/products.py` and `models/promotions.py` into `domains/catalog/models/`.
3. Rewrite imports:
   - `from services.catalog.X` → `from domains.catalog.services.X`
   - `from models.products` → `from domains.catalog.models.products`
   - `from models.promotions` → `from domains.catalog.models.promotions`
4. Remove root `services/catalog/` and root `models/products.py` / `models/promotions.py`.
5. Move `controllers/catalog/*` to `modules/catalog/routers/` (already done; remove root `controllers/catalog/`).
6. Boot-test.

### Phase 3 — Remaining domains (one by one)
Same pattern as catalog, ordered by size (smallest first to minimize blast radius):
1. `customers` (14 files in domains/, 5 in services/, 1 controller)
2. `payments` (14 files)
3. `accounts` (33 files)
4. `media` (29 files)
5. `hr` (38 files)
6. `logistics` (32 files)
7. `suppliers` (31 files)
8. `comms` (55 files)
9. `country` (55 files)
10. `orders` (52 files)
11. `governance` (91 files)
12. `finance` (87 files)

### Phase 4 — Controllers: complete the 13 remaining
- Relocate the 13 controllers still in root `controllers/` per Table 2.
- Retarget `auto_router.py` `CONTROLLERS_DIR` from `controllers` → `modules`.
- Regenerate routers: `python routers/generated/auto_router.py`.
- Update `main._load_routers()` to also glob `modules/**` (in addition to `routers/**`).
- Boot-test.

### Phase 5 — Routers split
- Hand-written routers in `routers/` are split into `modules/{module}/routers/` by actor.
- Generated routers are regenerated from `modules/` controllers.
- Root `routers/` becomes a legacy shim layer.

### Phase 6 — Cleanup
- Remove root `services/`, `controllers/`, `models/`, `routers/` (or move to `_legacy/`).
- Verify final boot and route count matches baseline.

---

## Risk Register

| Risk | Mitigation |
|---|---|
| Import rewire breaks a file the rewriter missed | Boot-test after EVERY domain. If green, proceed; if red, revert that domain only. |
| Two services in different domains have the same name | Use fully-qualified import paths in rewrite rules. |
| `models/__init__.py` is a registry; removing it breaks `from models import X` | Keep root `models/__init__.py` as a re-export shim during transition, then remove once all importers are rewired. |
| `auto_router.py` generator retarget breaks router discovery | Regenerate and run `--verify` in CI; `_load_routers()` is crash-proof per existing guards. |
| Circular imports appear after rewire | Use AST rewriter to detect and flag cycles before writing. |

---

## Next Move

Start **Phase 2 — catalog domain pilot**. Move services/catalog/ + models/products.py + models/promotions.py into domains/catalog/, rewrite imports in all affected files, boot-test.
