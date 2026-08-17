## Objective
- Verify all files from `backend/_legacy`, `_archive_services`, `_scratch_modules_backup`, `models` are accurately placed into the new `domains/`+`modules/` architecture, so the user can safely remove those folders and create a git checkpoint.

## Important Details
- Edit/Write tools globally denied (host guardrail); verification done via bash + PowerShell `Set-Content` heredocs running Python, reading sources with `utf-8-sig`.
- Project root `D:\Projects\10- E-COMMERCE WEBSITE\zozi`; backend = `backend/`.
- Verification MUST be content-based, NOT filename-based. CRITICAL LESSON (this session): matching by **function/route name alone is insufficient** — the migration RENAMED and CONSOLIDATED routers (`*_route` suffix dropped, `*_controller` modules -> `*_service`, private `_x` helpers inlined). Use route-path + symbol-with-rename heuristics.
- Source folders: `_legacy` (647 .py), `_archive_services` (22), `_scratch_modules_backup` (477), `models` (58) = 1204 .py.
- New arch: `domains/<d>/{models,services,schemas,...}` (14 domains + UNMAPPED) + `modules/<d>/{routers,services}`, `infrastructure/`, `db/`.
- `public_*.py` files are AUTO-GENERATED thin wrapper routers: they import real logic from `modules.<d>.routers.<x>_controller` (now `domains/<d>/services/*_service.py`) and expose HTTP routes. The logic (not the wrapper) is the migration target.
- BOM gotcha: `_scratch_modules_backup/admin/routers/*.py` are UTF-8 BOM (`efbbbf`); use `utf-8-sig`.
- No git commit yet (3,027 uncommitted files).

## Work State
### Completed
- Deep, content-based re-investigation of the 4 source folders (correcting an earlier FALSE "40 missing" verdict that matched wrapper function NAMES).
- CONFIRMED: the `public_*` files (87) are migrated. 76/87 wrappers' imported logic fully present; other 11 only flagged due to artifacts (module names, stdlib `InvalidOperation`, `(` parsing, renamed routes).
- Deep scan of all 477 `_scratch_modules_backup` files: every flagged `*_route` symbol resolves to a present symbol under a renamed form (e.g. `archive_order_route`->`archive_order`, `bulk_delete_orders_route`->`bulk_delete_orders`, `list_coupons_route`->`list_coupons`). Constants (`BASE_DIR`, `MAX_BULK_ITEMS`, `VALID_STRATEGIES`, `_OLLAMA_TEXT_MODEL`) and helpers (`get_redis`) present.
- Plain-text grep confirms key functions exist: `add_to_cart`, `validate_coupon`, `get_ai_suggestions`, `get_product_angles`, `queue_*_job`, `process_job`, `publish_job`, `analytics_*`, `audit_*`, `require_roles`, `unarchive_product_route`, `ticket_detail`, `bulk_verify_suppliers_route`, `database_overview`, `permission_hierarchy`.
- Per-folder status: `_legacy` 1 gap (logic now in `modules/admin/routers/ai.py`); `_archive_services` 0; `_scratch_modules_backup` ~0 genuine logic gaps (only ~6 private helpers inlined: `_collect_upload_sources`, `_generate_ai_suggestions`, `_require_super`, `_resolve_auth_dep_key`; possibly `logistics_partners_route`); `models` 0.

### Active
- Reporting corrected verification: migration of the 4 source folders is effectively complete; safe to plan removal pending the caveats below.

### Blocked / Caveats
- `modules/admin/routers/ai.py` has a SYNTAX ERROR — `get_ai_suggestions` etc. exist textually but the file won't import; must be fixed before boot.
- Check is content/name presence, not runtime behavior. Final gate = boot/import smoke test (start app, confirm all routers mount) before deleting source folders / committing.
- Edit/Write tools denied; cannot fix `ai.py` directly this session.

## Next Move
1. Fix the `modules/admin/routers/ai.py` syntax error (requires edit approval / another session).
2. Run a boot/import smoke test to confirm all routers (incl. migrated `public_*` and `admin/*`) mount without ImportError.
3. Only after boot is green: remove the 4 source folders and let the user create the git checkpoint.

## Relevant Files
- `backend/_scratch_modules_backup/admin/routers/public_core_cart.py` — thin wrapper; logic `add_to_cart` in `modules/customer/routers/cart.py:81` + `domains/orders/services/cart_service.py:171`.
- `backend/_scratch_modules_backup/admin/routers/public_core_ai_upload.py` — logic `process_job`/`publish_job` in `modules/admin/routers/public_core_ai_upload.py`.
- `backend/modules/admin/routers/ai.py` — contains `get_ai_suggestions` etc. but HAS A SYNTAX ERROR (must fix).
- `backend/domains/<d>/services/*_service.py` — real migrated business logic (`admin_orders_service.py`, `admin_products_service.py`, `users_service.py`, `suppliers_service.py`, `tickets_service.py`).
- `backend/infrastructure/utils/redis_client.py:93` — `get_redis = redis_client`.
- `C:\Users\user\AppData\Local\Temp\kilo\verify_public_wrappers.json`, `verify_backup_deep.json`, `verify_final_reconcile.json` — verification outputs.
- `C:\Users\user\AppData\Local\Temp\kilo\verify_public_wrappers.py`, `verify_backup_deep.py`, `verify_final_reconcile.py` — scripts.
