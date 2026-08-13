# Project Status — ZOZI architecture audit & layered-extraction plan

## Goal
- Audit the FastAPI backend for correct layering (`routers → controllers → services → providers/models`, plus `middleware`/`dependencies`) and extract logic into the correct layer; plan and begin remediation without committing.

## Constraints & Preferences
- Do NOT commit (working tree only).
- AST/behavior-preserving changes; verify with `--check`/`--verify`, `py_compile`, app boot.
- Avoid huge file reads; bounded Grep/Read. PowerShell: no `&&`/heredoc; `;` + temp `.py` + set PYTHONPATH.

## Progress
### Done
- **Auto-router migration (prior work, complete):** all decorated controllers are auto-gen ready — 0 `skip=True` remain; 28 modules / 193 routes; `--check` & `--verify` OK; app boots (1423 routes).
  - Migrated last 5 routes: 4 promotion by-country (`/admin/{code}/...`) + reviews `PUT /api/v1/reviews/{review_id}`. Removed legacy `country_router` from `routers/admin_promotions_routes.py` and its `main.py` mount; module now emits a no-prefix (full-path) router in `routers/admin_commerce_promotion_admin.py`. RLS is a runtime no-op (`instrument_rls` never called) so the `set_rls_context` wrapper removal is behavior-preserving.
- **Safe broken-code fixes (this turn):**
  - `main.py` `/health/ready`: `db` was undefined → now opens a `get_db()` session; removed unused `from types import SimpleNamespace`.
  - `services/supplier/onboarding_pipeline.py`: `from providers.media import cv2` (broken — `providers/media/__init__.py` only binds `_cv2`) → `import cv2`.
  - `dependencies/coi_dependency.py` & `middleware/coi_middleware.py`: `user.get("id")` (AttributeError on ORM user) → `uid = user["id"] if isinstance(user, dict) else getattr(user, "id", None)`.
  - `middleware/country_context.py`: added missing `from services.hr.coi_service import check_approval_blocked` (latent NameError). App re-booted OK (1423 routes), no circular import.

### In Progress
- (none actively being edited now; planning phase) — see TODOs below.

### Blocked
- (none)

## Audit Findings (verified by parallel explore agents + direct grep)
- **Routers (207 files, 179 hand-written + 25 auto-generated):** ~72 hand-written routers still contain logic — direct `db.query`/ORM, business computations, or provider/SDK calls instead of delegating to controllers→services. Concentrated in treasury/finance (`admin_treasury_reporting`, `admin_treasury_status`, `admin_finance_creation`, `finance_package`, `governance_package`), `system_ai_*`, `supplier_*`, `security_*`, `geography_*`, `comms_*`, `admin_orders_status` (RLS duplication ×6), `admin_media_geography`, `admin_logistics_operations`, `system_comms_status` (WS state machine). ~107 routers are pure thin-wiring (good).
- **Controllers (177 files):** 2 do direct DB queries (most impactful): `controllers/customer/users.py` (826 lines, 21 `db_read` calls, N+1 loops, 61 model imports, `get_password_hash`/crypto) and `controllers/security/admin_users.py` (4 `db_read` + `selectinload` NameError). `finance/accounting_controller.py` + `finance/sub_ledger_controller.py` trigger indirect commits via `audit_log`. **0 controllers call external SDKs directly** (good funnel through services→providers). 29 controllers on auto-router; ~30 not, but most are thin facades; ~6 have real handler logic.
- **Services (495 files):** **0 ORM models defined in services** (no `__tablename__`; only 62 Pydantic DTOs — a convention decision). **BUT services contain provider implementation that duplicates existing providers:** `services/gateways/payments.py` re-implements PayPal/Tap/PayTabs/Thawani/Generic gateway HTTP calls with direct `httpx` (lines ~856, 2772, 2960, 3107, 3136, 3233, 3320, 3389, 3472, 3665, 3705, 3886, 4214, 4440) while `providers/payments/{paypal,tap,paytabs,thawani,generic}.py` already implement identical signatures. `services/common/command_center_service.py` `NewsAggregatorService` uses direct `httpx` (no News provider exists). Also `from db.base import Base` (empty second base) in several services.
- **Providers (71 files):** Mostly complete & wired — AI/Ollama/HuggingFace (`providers/ai/*`), OCR/`bg_remover`/parcel (`providers/image/*`), Stripe (partial — uses `providers.payments.stripe_sdk`), PayPal/Tap/PayTabs/Thawani/Generic (exist but UNUSED by services), email (Resend/SMTP), Twilio SMS/voice, geo/map/IP (`providers/geography/*`), OAuth/JWT/TOTP (`providers/auth/*`), scheduler, web search, video transcription. **GAPS:** no Apple OAuth provider anywhere; no News/RSS provider.
- **Models (58 files):** **CLEAN** — 0 business logic, 0 ORM models outside `models/`, 0 model→service imports. Minor: `models/payments.py` env-based table-args at import; `models/mixins.py` duplicates `db/mixins.py`.
- **Wiring & Middleware:** Router loading (`main._load_routers` glob) and middleware ordering (`orchestrator.setup_middleware`) are sound (0 missing modules; 205/205 routers import). **Critical bug:** TWO independent `DeclarativeBase`es — `models.Base` (real, 318 tables) vs `db.base.Base` (empty). `conftest.py`, `utils/schema_audit.py`, `services/admin/database_service.py`, `services/comms/communication_read_service.py`, `services/commerce/promotion_service.py` use the empty one → no-op metadata ops / broken test tables. **Security gap:** `WebhookVerificationMiddleware`/`WebhookIPWhitelistMiddleware` exported but never wired (payment/email webhooks unverified). `middleware/country_context.py:400` `check_approval_blocked` was undefined (fixed). Active middleware (`impossible_travel_middleware.py`, `country_context.py`) import `models` + run `db.query` (should move to services). `middleware/coi_middleware.py` is a duplicate of `dependencies/coi_dependency.py` (kept — still referenced). `db/database_logging.py` is referenced (not orphan). `rls_dependency.get_country_scope` is a no-op stub.

## Key Decisions
- Treat DTOs (Pydantic `BaseModel`) living in `services/` as an accepted convention (218-ish total; 62 in services) — not a violation; defer the "where do DTOs live" decision.
- Payment-gateway provider extraction must **verify parity** before switching (the service re-implementations may have diverged from providers); do not blindly reroute the live payment path.
- Two-base fix preferred approach: make `db/base.py` re-export `models.Base` (single source) — but verify no circular import (`models` does NOT import `db.base`, so safe in principle; test at boot). Alternatively update each consumer. Lower-risk: keep `models.Base` as canonical and alias `db.base.Base = models.Base`.
- `email_service.py`, `coi_middleware.py`, `database_logging.py` are referenced — do NOT delete (verified).
- `_services_bak/`, `_routers_clean/` are backup dirs — unreferenced; candidate removal but low priority.

## TODOs (see todo list)
1. (done) Safe broken-code fixes.
2. Collapse two declarative bases.
3. Services→Providers: payment gateways (route through existing providers + parity check); add News provider.
4. Controllers→Services: `customer/users.py`, `security/admin_users.py` off direct db.query.
5. Routers→Controllers/Services: extract logic from ~72 logic-containing routers.
6. Controllers auto-gen readiness: migrate ~6 real-logic controllers.
7. Providers completeness: Apple OAuth + News provider.
8. Middleware cleanup: move fraud/country resolution to services; wire WebhookVerification; fix rls_dependency stub; relocate behavioral_analytics/siem_engine.
9. Models minor: env-based table-args helper; consolidate mixins.
10. Module-by-module advanced investigation (commerce, finance/treasury, supplier, logistics, security, geography, comms, ai, hr, admin).
11. Remove dead backups/orphans (verify unreferenced first).

## Critical Context
- App boots: **1423 routes**, 0 failed routers. ~97 pre-existing duplicate (METHOD,path) registrations across legacy-vs-generated routers (tolerated by FastAPI; not introduced by recent changes — verified the 5 migrated routes each register exactly once).
- Generator: `_existing_routes` reads only the FIRST `APIRouter(prefix=...)` per file (re.search) → misses secondary routers; skips `AUTO-GENERATED` MARKER files. Generated routers written to `routers/` surface, auto-discovered by `main._load_routers()` glob `routers/**/*.py`.
- `instrument_rls` (rls_interceptor.py:359) never called → RLS no-op at runtime.
- Current verified: `--check` 28 modules/193 routes OK; `--verify` in sync; 0 `skip=True`.

## Relevant Files
- `backend/main.py` — `/health/ready` fix (lines ~112-149); `_load_routers()` (194-226); removed country_router mount.
- `backend/services/supplier/onboarding_pipeline.py` — cv2 import fixed (line 15).
- `backend/dependencies/coi_dependency.py`, `backend/middleware/coi_middleware.py` — COI `.get("id")` fix.
- `backend/middleware/country_context.py` — added `check_approval_blocked` import.
- `backend/services/gateways/payments.py` — duplicated gateway impls (target for provider extraction).
- `backend/providers/payments/{paypal,tap,paytabs,thawani,generic}.py` — existing impls to reuse.
- `backend/controllers/customer/users.py`, `backend/controllers/security/admin_users.py` — direct DB queries (target for service extraction).
- `backend/db/base.py` vs `backend/models/__init__.py` — two-base bug.
- `backend/routers/admin_promotions_routes.py` — now only `/health`+`/status` probes.
- `backend/routers/admin_commerce_promotion_admin.py` — generated, 11 promotion routes (full-path).
- `backend/routers/generated/auto_router.py` — generator (prefix/kw-only fixes).
- `backend/routers/generated/AUTO_ROUTER.md` — doc (updated with promotion migration).
