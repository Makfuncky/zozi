# Session note — DOM3 resolution (2026-08-10, ~19:25)

## Finding
`DOM3 | controllers | backend\controllers\admin` — SURFACE folder 'admin/'
inside the DOMAIN layer controllers/. The detector flags any folder named as a
surface (admin/customer/supplier/...) inside a domain layer that is not a
registered domain.

## Verification
- `controllers/admin/` held 13 files (4,372 lines) — the legacy admin monolith,
  live via the `controllers.admin_controller` facade (38 importers).
- The domain folders ALREADY held canonical, newer implementations (new
  `data.models`/service conventions): security/admin_auth.py, customer/users.py,
  orders/orders.py, catalog/products.py, permissions/permissions.py,
  audit/misc.py, analytics/analytics.py, etc. Verified behavior-equivalent for
  the live symbols (update_user_role, toggle_user_active, update_order_status
  differ only by the `first()` helper / service delegation — the W1-correct
  refactor).
- The facade isolated ALL external imports: only the facade + 1 intra-package
  import + 2 test assertions referenced the subpackage internals.

## Fix (atomic migration, zero behavior change for consumers)
1. **Facade rewritten** (`controllers/admin_controller.py`) — explicit
   re-exports from the canonical domain controllers (security, customer,
   catalog, orders, commerce, supplier, treasury, comms, configuration,
   analytics, audit, permissions) + services.admin_analytics_service +
   utils.admin_shared. All 85 legacy public symbols preserved (verified via
   AST + runtime getattr).
2. **Deleted `controllers/admin/`** (13 files + __init__) after the deletion
   gate: zero live references outside the facade (remaining refs are
   docstrings + already-migrated test assertions).
3. **Tests updated** (`backend/tests/test_controller_subpackages.py`) — the
   Admin classes now assert the migrated structure (facade sources from domain
   folders; controllers/admin/ gone; canonical files present). 18/18 pass.

## Churn repairs required to verify (genuine defects, reported per process)
The concurrent agent's codemod had broken the ENTIRE backend import chain.
Repairs made (all mechanical / name-correctness):
- **171 model classes** across models/ had `{"schema": ...}` dicts mid-tuple in
  `__table_args__` (invalid SQLAlchemy; broke `import models`). Fixed via
  `_extra_files/fix_table_args.py` (AST + source-splice; moves dict to tuple
  end). The agent's codemod re-ran once mid-turn (18:57 batch, then a new
  tuple-concat variant in payments.py at 19:06) — fixed the concat variant too.
- `services/misc_write_service.py` — stale `from db.seed import
  ensure_demo_user, seed_password` (now `_ensure_demo_user`, `_seed_password`)
  and stale `utils.soft_delete` names (`has_soft_delete`/`now` →
  `_has_soft_delete`/`_now`).
- `controllers/catalog/products.py` — `bump_product_cache_version` →
  `_bump_product_cache_version`.
- `controllers/customer/users.py` + `controllers/security/admin_users.py` —
  wrong-name imports (`_build_user_delete_blocker`,
  `_delete_order_records`, `_hard_delete_user_record` →
  `build_user_delete_blocker`, `delete_order_records`,
  `hard_delete_user_record`).
- `services/finance/order_payment_functions.py` — alias
  `event_publisher as _event_publisher`, `order_holds_inventory as
  _order_holds_inventory` (shim __all__ + consumers expect underscores).
- **Created missing `services/orders/orders_write_service.py`** — a phantom
  module referenced by `controllers/orders/orders.py` and the
  `services.orders_write_service` shim that NEVER existed in git. Implemented
  the 5 row-writers (create_order, create_order_item, update_order,
  delete_order, delete_order_with_savepoint) from the usage contracts.
- `models/__init__.py` — re-added `from .erp import *` + 13 ERP class names
  (the agent's rewrite dropped the ERP wiring; `routers/system_ai_reporting`
  needed PurchaseOrder).

## Validation
- DOM3 detector replica + authoritative audit: **DOM3 absent (1 → 0)**.
  RED total **1419 → 1283** (agent's migration + these fixes also reduced
  CG1/CG2/W1/W3/SEC).
- Facade runtime check: all 21 live consumer symbols resolve; **11/11 sampled
  facade importers import cleanly** (including lifespan + auth_controller).
- Tests: test_controller_subpackages 18/18; regression suites (CA3, LC1, MW3,
  PERF2, SEC5) pass. Pre-existing failures NOT caused by this change:
  `test_security_module.py` (utils.security_audit imports models at HEAD;
  routers/public_auth_access.py does not exist at HEAD).

## Notes for the agent
- `services/orders/orders_write_service.py` is new — review the
  delete_order_with_savepoint savepoint semantics against the old
  admin/orders.py `db.begin_nested()` pattern.
- The models codemod bug (schema dict placement) is systemic — if it re-runs,
  re-apply `_extra_files/fix_table_args.py`.
- `_extra_files/` scratch: verify_facade_ast.py, map_all_symbols.py,
  fix_table_args.py, scan_table_args_variants.py, find_bad_model.py.
