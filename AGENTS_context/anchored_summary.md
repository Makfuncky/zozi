## Goal
- (Task 1, DONE) Extract the admin controller layer (thin `@route`-decorated wrappers over existing services) so the auto-router generator can emit routers; solve the "56 missing admin_controller names" at the controller layer. Services were already complete in `services/admin/*`; 12 controller modules now exist in `controllers/admin/*_controller.py`.
- (Task 2, DONE) Verify completeness + accurate service→controller wiring + decorator correctness for auto-generation.
- (Task 3, OPEN) Wire the 12 new controllers into `routers/` WITHOUT clobbering hand-written routers.

## Constraints & Preferences
- Layered architecture: `models → services → controllers → routers`; routers auto-generated thin wrappers (generator scans `controllers/` via AST, never imports).
- Controllers import decorators ONLY from `routers.generated.auto_router` (`@get/@post/@put/@patch/@delete/@route`); must NEVER import FastAPI directly.
- `deps=["db","admin"]` only known auth dep keys; service funcs take `(db, ..., acting_user, ...)` with `acting_user` a dict.
- Generator rule: when `body` set there must be exactly ONE non-path/non-dep leftover param; extra leftovers via `query=[...]`.
- Keep app bootable; do NOT revert the 394 uncommitted refactor deletions.
- Do NOT run blanket regeneration that overwrites hand-written (non-`AUTO-GENERATED`) routers.

## Progress
### Done (Task 1 — extraction)
- 12 admin controller modules under `controllers/admin/`: products, orders, payouts, coupons, analytics, users_admin, suppliers, tickets, audit, permissions, misc, bank_accounts. Plus `controllers/catalog/category_admin_controller.py` (already present).
- `services/admin/*` complete (products, orders, payouts, coupons, misc, bulk_ops, permissions, suppliers, tickets, audit, users, analytics, admin_write, admin_fallback, database).

### Done (Task 2 — verification + fixes)
- Decorators validated project-wide via generator `--check`: 17 modules / 101 routes — OK (no duplicate routes, no forbidden patterns, body/leftover rule satisfied). Admin subset: 13 modules / 77 routes — OK.
- Generated routers emitted to a throwaway dir and compiled: 13/13 compile cleanly.
- AST wiring checker across all 13 admin controllers: **found 11 issues, all fixed**:
  1. `products_controller.py` + `orders_controller.py` imported `archive_entity/restore_entity/hard_delete_entity/bulk_archive_entities/bulk_restore_entities` from `controllers.admin.admin_controller`, but those live in `services.admin.misc_service` (`archive_entity`, `restore_entity`, `hard_delete_entity`) and `services.admin.bulk_ops_service` (`bulk_archive_entities`, `bulk_restore_entities`). Would have raised `ImportError` at boot. Fixed → imports now point at the service modules (matches architecture: controllers→services).
  2. `suppliers_controller.py` called `get_all_suppliers(db, limit=, offset=, search=)` but the service signature is `get_all_suppliers(db, *, skip=, limit=, q=, status=, badge=)`. Fixed → `skip=offset, q=search`.
- After fixes: wiring checker = **0 issues** across 13 controllers; the 3 fixed controllers import at runtime (`IMPORT OK`) — no ImportError.

### Open (Task 3 — router integration)
- Controllers are ready, but generated router files for them are NOT yet in `routers/` (a blanket regen clobbers 19 hand-written routers). Need a safe emit (only new controllers' routers, skip/merge hand-written).

## Key Decisions
- Repointed archive-helper imports to the service modules rather than adding re-exports to `admin_controller.py` (cleaner; controllers depend on services, not other controllers).
- Did NOT revert the 394 uncommitted refactor deletions; kept the 12 new controllers.
- Avoided blanket regen (it clobbers hand-written routers: 203→188 routes, 10→20 failures). Baseline committed routers = 203 routes / 10 pre-existing failures.

## Next Steps
- Generate only the 12 new controllers' routers without overwriting hand-written ones (modify generator to skip non-`AUTO-GENERATED` files / emit to a new surface, or manually create `AUTO-GENERATED`-marked routers).
- For payouts: both routes collide with hand-written `admin_treasury_status.py` (pre-existing failure at HEAD).
- Boot app post-integration; confirm route count rises above 203 with no new failures.
- Optionally fix the 10 pre-existing failing routers.

## Critical Context
- Repo root: `D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend`. venv: `backend\venv\Scripts\python.exe`.
- Generator: `routers/generated/auto_router.py`. Modes: `--check` (validate+summary, exit 1 on fail), `--report` (list routes), `--dry-run`, `--verify` (CI gate vs committed), `--domain <substr>` (filter), `--out <dir>` (safe emit elsewhere), `--backup`, `--force` (emit colliding).
- Generator contract: path `{name}`→path param; `deps`→injected; `query`→query param; leftover with `body`→body; leftover else→bodyfield (write)/query (read). `KNOWN_DEPS`: db, admin, user, optional_user, background_tasks, request.
- Files changed this session: `controllers/admin/products_controller.py`, `controllers/admin/orders_controller.py`, `controllers/admin/suppliers_controller.py`.

## Relevant Files
- `controllers/admin/*_controller.py` (13 modules): deliverable; decorators validated, wiring fixed.
- `services/admin/misc_service.py`: `archive_entity` (L52), `restore_entity` (L90), `hard_delete_entity` (L112).
- `services/admin/bulk_ops_service.py`: `bulk_archive_entities` (L17), `bulk_restore_entities` (L40).
- `services/admin/suppliers_service.py`: `get_all_suppliers(db, *, skip, limit, q, status, badge)` (L492).
- `routers/generated/auto_router.py`: decorator contract + generator (do not let it overwrite non-`AUTO-GENERATED` routers).
- `controllers/catalog/category_admin_controller.py`: proven reference pattern.
