# Architecture Audit + Auto-Router — Anchored Summary

## Goal
- Multi-layer architecture audit (routers/services/controllers/models/providers/middleware) for layer violations + plan & implement auto-router generation from controllers, including RBAC `permissions` support and resolving flagged wiring/provider-extraction gaps.

## Constraints & Preferences
- Routers THIN (APIRouter + decorators + delegation); NO inline DB, NO ORM models, NO provider/external code (W1 gate).
- Controllers declare HTTP contract via `routers.generated.auto_router` metadata only — never import FastAPI; NO inline DB, NO ORM models, NO `APIRouter`.
- Services = business logic + DB; MUST call providers, not embed external SDKs inline.
- Providers = ALL external integrations. `services/gateways/*` accepted gateway layer (out of scope for Audit #7).
- `main.py` only mounts `routers.*`; `services/location_service` exempt from no-`APIRouter` rule.
- Router loader uses `glob.glob("routers/**/*.py")` — `.bak` inert but clutter; `_routers_clean/` & `_services_bak/` at backend root are full backups (inert).

## CONTROLLER / AUTO-GEN LANDSCAPE (verified 2026-08-12)
- 62 "real" controller modules exist (excluding `controllers/delegators/` which has 94 service-shim files).
- 26 carried `@route` metadata (173 generated routes). After this session: 27 (analytics_fallback_controller added).
- 36 remained WITHOUT metadata. Categorization:
  - **6 "PROPER"** (explicit handler functions): `admin.analytics_fallback_controller` (DONE), `admin.auth` (DEPENDENCY module — exposes `require_admin`/`get_current_admin`, NOT routes → exclude), `comms.chat_write_controller`, `customer.users`, `governance.command_center_controller`, `security.admin_users`.
  - **1 HOLLOW** re-export shim (`products.products_controller` — enumerates `services.*` into `globals()`).
  - **29 EMPTY** re-export shims (no functions; re-export service API, served by DYNAMIC routers that build routes from `dir()`).
- KEY FINDING: most "remaining" controllers are NOT simple handler modules. They are re-export shims behind **dynamic/mixed-proxy routers**. "Auto-gen ready" for them requires CREATING explicit `@route` wrapper functions + DECOMPOSING the dynamic/mixed routers — not just adding decorators.
- Generator behavior: `generate_router_file` SKIPS any route that collides (same METHOD+path) with an existing committed (hand-written) router. So adding metadata is SAFE (collision → skip); decommissioning hand-written routers is the risky step.
- `admin_analytics_fallback_dashboard.py` is a MIXED proxy: delegates to `analytics_fallback_controller` (5 fns) AND `admin_controller.get_all_suppliers` AND inline DB logic (suppliers/payouts/categories/employees/payments/logistics/logistics-partners). DO NOT delete wholesale — would drop those fallback routes.

## Progress
### Done
- Auto-router RBAC extension (prior): `require_permissions(slugs)` in `utils/dependencies.py`; generator emits `permissions=[...]`; demo on `controllers/admin/audit_controller.py`; `--check`/`--verify` pass.
- Audit #7 stripe fix (prior): `providers/payments/stripe.py::refund_payment_intent`; `services/admin/orders_service.py` delegates.
- Middleware layer-order inversion fix (prior) + verified in `test` env.
- Audits #3,#4,#5,#6 CLEAN.
- Audit #1 partial: `routers/admin_analytics_fallback_dashboard.py` inline SQLAlchemy extracted into `services/admin/analytics_fallback_service.py` + `controllers/admin/analytics_fallback_controller.py` (prior session); this session ADDED `@route` metadata to the 5 handler functions; `--check` passes (5 routes, collide-safe).
- Audit #7 detailed findings documented.

### In Progress
- "Complete remaining controllers → auto-gen ready" (user scope: all 36 real). Investigation done; 1 of 36 completed (analytics_fallback_controller). BLOCKED on safe execution of the other 35 due to hollow/dynamic-router structure.

### Blocked
- Middleware production verification: `APP_ENV=production` raises `FIELD_ENCRYPTION_KEY required` (utils/config.py:237) + `SENTRY_DSN required` when absent.
- Safe migration of the 30 hollow/empty + mixed-proxy controllers (needs explicit handler wrappers + dynamic-router decomposition).

## Key Decisions
- Subagent audit approach FAILED earlier (codebase too large). Direct grep used instead.
- Audit #1 fixed by extracting to service+controller (thin router delegates).
- `providers/image/bg_remover.py` DEAD (no importers); duplicates live cv2 in `services/ai`.
- For the 36 controllers: adding `@route` metadata is safe (generator skips collisions); DELETING hand-written routers is dangerous (mixed proxies). Plan = annotate first, decommission per-router after decomposition.

## Next Steps
1. **Handler controllers (safe, do next):** add `@route` metadata to `comms.chat_write_controller`, `customer.users`, `governance.command_center_controller`, `security.admin_users`, mirroring EXACT paths/methods/auth from their serving routers (`system_comms_status.py`, `admin_identity_operations.py`, `admin_logistics_operations.py`, dynamic command-center router). Do NOT delete those routers yet.
2. **Hollow/empty controllers (deeper):** for `products.products_controller` + 29 empty shims, CREATE explicit `@route` wrapper functions delegating to the re-exported service functions, matching the dynamic router's produced paths. Requires reading each dynamic router.
3. **Decompose mixed-proxy routers:** split `admin_analytics_fallback_dashboard.py` (and similar) so analytics_fallback routes come from the controller's generated router and the rest move to their owning controllers; only then delete the hand-written proxy.
4. **Audit #7 provider extraction:** move cv2 from `services/ai`, `services/common/free_image_tools.py`, `services/supplier/*` into `providers/image`; make services delegate.
5. **Verify:** `python routers/generated/auto_router.py --check` + `--verify`; app import smoke test; green `tests/test_architecture_gates.py`.

## Critical Context
- `SURFACES` in auto_router.py maps path-prefix → auth dependency (`get_current_admin`/`get_current_user`/`get_current_user_optional`) + backing module.
- `@get/post/put/patch/delete(path, deps=[...], query=[...], body=<Model>, response_model=<Model>, tags=[...], permissions=[...], status_code=..., rls=..., skip=...)`.
- `deps` tokens: `db`→`Depends(get_db)`, `admin`→`require_admin`, `user`→`get_current_user`, `optional_user`→`get_current_user_optional`, `background_tasks`, `request`.
- Generated wrapper signature: path params → path; leftover POST/PUT/PATCH args → body fields; GET leftover args → query; ends with `current_user=None, db: Session = None`.
- Generated file name: `{surface}_{feature}_{domain}.py` in `routers/`; never overwrites non-marker files; collision routes skipped.
- Run: `cd backend; python routers/generated/auto_router.py --check|--verify|--report [--domain <substr>]`.

## Relevant Files
- `controllers/admin/analytics_fallback_controller.py` — now has `@route` metadata (1 of 36 done).
- `services/admin/analytics_fallback_service.py` — data layer for the above.
- `routers/admin_analytics_fallback_dashboard.py` — MIXED proxy; do NOT delete wholesale.
- `controllers/products/products_controller.py` — HOLLOW re-export shim (globals() enum).
- `routers/generated/auto_router.py` — generator + decorators (lines 1-660 emit logic; 720-778 verify).
- `controllers/admin/coupons_controller.py` — REFERENCE template for proper metadata style.
- `providers/image/bg_remover.py` — dead; Audit #7 target.
- `services/ai/bg_removal_service.py`, `services/common/free_image_tools.py`, `services/supplier/onboarding_pipeline.py`, `services/extracted/supplier_supplier_upload_service.py` — cv2 leaks (Audit #7).
