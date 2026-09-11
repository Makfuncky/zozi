```
=== AGENT LOG ===
PHASE: 04 — Import / Module Dependency Map
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_04_IMPORT_MAP.md
SCOPE_COVERED: Backend Python import graph (domains/, modules/, kernel/, infrastructure/, rbac/, providers/, middleware/, jobs/, lifespan.py, main.py, config) and frontend/web_app/src (lib/, app/, components/, shared aliases). Focus on application-level import edges, hubs, cycles, orphans.
FILES_EXAMINED: ~40 opened in full/part + import-frequency scans across ~1560 backend .py and ~752 frontend .ts/.tsx
EVIDENCE_ITEMS: ~95 file:line citations
FINDINGS_TOTAL: 27  (VERIFIED: 24 / INFERRED: 3 / UNKNOWN: 0)
SEVERITY_BREAKDOWN: BLOCKER: 0 / HIGH: 3 / MEDIUM: 6 / LOW: 5 / INFO: 13
TOP_FINDINGS:
  1. infrastructure/database/database.py is the #1 hub — 339 imports across 241 files — backend/infrastructure/database/database.py:1
  2. domains/governance/ports.py eagerly imports 7 sibling domains' models at top level while imported by ~10 domains (cycle nexus) — backend/domains/governance/ports.py:42-52
  3. Package-level cross-domain cycles are real (accounts<->governance, accounts<->catalog, security<->governance, suppliers<->governance, promotions<->governance, comms<->governance, finance<->governance, accounts<->customers) — evidence per edge below
  4. Cross-domain WRITE decoupling is via in-process event_bus (publish/subscribe); READS via ports.py — backend/infrastructure/messaging/events/event_bus.py:1-29
  5. Contradiction: main.py:12 claims models "registers all ORM models" but models.py only clear_mappers() — backend/infrastructure/database/models.py:1-16 vs backend/main.py:11-12
  6. Frontend hub @/lib/api imported by 200+ files; @/lib/useAuth second — frontend/web_app/src/lib/api/index.ts:1-9
  7. rbac.dependencies (require_feature/get_current_user) imported by ~110 router files — backend/rbac/dependencies.py:10-13
  8. Contradiction: accounts/models/user.py:20 comment says "Lazy imports" but lines 21-22 are eager top-level imports — backend/domains/accounts/models/user.py:20-22
GAPS / NOT DETERMINABLE: Dynamic/runtime import ordering deadlocks not proven (would require executing the lifespan preloader); frontend runtime bundling graph (webpack) not traced beyond static import edges; test/migration/script files intentionally de-emphasized.
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 04 — IMPORT / MODULE DEPENDENCY MAP (Zozi)

> Forensic, evidence-based. Every claim cites `file:line`. Labels: **VERIFIED**
> (read from source), **INFERRED** (strongly implied by aggregated evidence),
> **UNKNOWN**. Import *edges* are static (top-level unless noted "lazy" =
> function-local / `TYPE_CHECKING`). Counts come from repo-wide `grep` of import
> statements; where a scan truncated, the reported file/match count is the
> tool's stated total (e.g. "339 matches in 241 files").

## 0. Method & grounding

- Backend is Python/FastAPI, layered: `kernel/` (leaf primitives) → `infrastructure/`,
  `providers/` → `domains/*` → `rbac/`, `middleware/` → `modules/*` (role routers) →
  `main.py`/`lifespan.py`/`jobs/`. An **enforced** import-direction law exists:
  `backend/tests/system/test_import_direction_all_packages.py:1-22`,
  `backend/tests/_support/laws.py:60-70` (`FORBIDDEN_IMPORT_RULES`). **VERIFIED.**
- Cross-domain **reads** are routed through each domain's `ports.py`
  (`backend/domains/governance/ports.py:1-8`, `backend/domains/accounts/ports.py:1-9`). **VERIFIED.**
- Cross-domain **writes** are decoupled via an in-process event bus
  (`backend/infrastructure/messaging/events/event_bus.py:1-29`): every domain has
  `events.py` (publish) + `subscribers.py` (subscribe). **VERIFIED.**
- Frontend Next.js under `frontend/web_app/src` with two path aliases: `@/*` → `src/*`
  and `@shared/*` → sibling `frontend/shared` package
  (`frontend/web_app/src/lib/api/client.ts:6-11`, `frontend/web_app/src/lib/useAuth.tsx:12-22`). **VERIFIED.**

---

## MODULE INVENTORY

Legend: Internal Deps = first-party workspace imports; External Deps = 3rd-party/framework
(stdlib omitted). "→ N/M" for hubs means N import statements across M files.

### Backend — foundation / infrastructure hubs

| File | Key Imports | Internal Dependencies | External Dependencies | Exports (symbols) |
|---|---|---|---|---|
| [backend/config.py](backend/config.py) | canonical settings source | (leaf) | pydantic/pydantic-settings (INFERRED) | `settings`, `BASE_DIR`, app config |
| [backend/infrastructure/utils/config.py](backend/infrastructure/utils/config.py#L1-L2) | `from config import *` | `config` | — | re-export shim of `settings`,`BASE_DIR` |
| [backend/infrastructure/config.py](backend/infrastructure/config.py#L7) | `from infrastructure.utils.config import *` | `infrastructure.utils.config`→`config` | — | 2nd re-export shim (3 paths → 1 source) |
| [backend/infrastructure/database/base.py](backend/infrastructure/database/base.py#L1-L7) | SQLAlchemy `DeclarativeBase` | (leaf) | sqlalchemy | `Base` |
| [backend/infrastructure/database/database.py](backend/infrastructure/database/database.py#L26-L28) | config + base | `infrastructure.utils.config`, `infrastructure.database.base` | sqlalchemy (sync+async) | `engine`,`SessionLocal`,`get_db`,`get_db_context`,`get_service_session`,`get_db_session`,`create_tables`,`check_connection_health`,`get_pool_metrics`,`_engine`,`_IS_SQLITE`,`Base` (re-export) |
| [backend/infrastructure/database/models.py](backend/infrastructure/database/models.py#L11-L16) | only `clear_mappers()` | sqlalchemy.orm | sqlalchemy | (side-effect only; imports NO domain models — see Contradiction C1) |
| [backend/infrastructure/messaging/events/event_bus.py](backend/infrastructure/messaging/events/event_bus.py#L11-L29) | stdlib only | (leaf, "circuit-exempt data layer") | — | `subscribe`,`publish`,`EVENT_ORDER_STATUS_CHANGED`,`EVENT_ORDER_REFUNDED`,`_subscribers` |
| [backend/middleware/orchestrator.py](backend/middleware/orchestrator.py#L46-L65) | 16 middleware classes + config | `middleware.*` (16 modules), `infrastructure.utils.config` | fastapi, starlette | `setup_middleware(app)` |
| [backend/lifespan.py](backend/lifespan.py#L21-L22) | models preload, DB, config | `infrastructure.database.*`, `infrastructure.utils.config`, `infrastructure.utils.migrations`, `domains.accounts.services.permissions.permission_service` | fastapi, structlog | `build_lifespan()`, `_preload_all_models`, `_on_startup_*` hooks |
| [backend/main.py](backend/main.py#L11-L40) | models(first), middleware, DB, RLS, obs, versioning | `infrastructure.database.*`, `middleware.orchestrator`, `infrastructure.observability.*`, `infrastructure.utils.*`, `lifespan` | fastapi, structlog | `app` (FastAPI), health routes |

### Backend — kernel (leaf primitives)

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [backend/kernel/money.py](backend/kernel/money.py#L1-L30) | stdlib `decimal` only | none | — | `to_decimal`,`round_money`,`to_cents`,`from_cents`,`money_to_minor_units`,`format_currency`,`MONEY_QUANT` |
| [backend/kernel/__init__.py](backend/kernel/__init__.py) | (empty) | none | — | none (submodules imported directly) |
| kernel/country.py, currency.py, numbering.py, period.py, constants.py, mixins.py | stdlib | none (INFERRED leaf) | — | `normalize_country`,`CountryCode`,`GCC_COUNTRIES`,`next_reference`,`fiscal_quarter`,`date_range` (per `backend/tests/kernel/test_kernel.py:100-280`) |

### Backend — rbac (authorization)

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [backend/rbac/dependencies.py](backend/rbac/dependencies.py#L10-L13) | catalog, resolution, security deps | `rbac.catalog`, `rbac.resolution`, `infrastructure.security.dependencies` | fastapi, contextvars | `require_feature`,`require_module`,`require_roles`,`require_admin`,`get_current_user`,`set_current_user`,`_ROLE_FEATURES`,`_ROLE_MODULES` |
| [backend/rbac/catalog.py](backend/rbac/catalog.py) | feature files scan | domain `features.py` (INFERRED) | — | `FEATURE_CATALOG`,`FEATURE_NAMESPACES`,`all_features`,`is_known`,`VALID_USER_ROLES` |
| [backend/rbac/resolution.py](backend/rbac/resolution.py) | — | (leaf-ish) | — | `expand_wildcards`,`effective_features` |

### Backend — domain ports (cross-domain READ facades)

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [backend/domains/governance/ports.py](backend/domains/governance/ports.py#L42-L52) | own + 6 sibling domains' models | `governance.models.admin`, `accounts.models.banking`, `accounts.models.user`, `suppliers.models.suppliers`, `suppliers.models.fraud_indicators`, `promotions.models.*`, `customers.models.customer_schema_models`, `security.models.fraud`, `comms.models.fraud`, `comms.models.incident`, `infrastructure.utils.pagination` | sqlalchemy | `User`, admin ops (`archive_entity`,`restore_entity`,`hard_delete_entity`,`export_*`), 30+ re-exported models |
| [backend/domains/accounts/ports.py](backend/domains/accounts/ports.py#L40-L45) | own models | `accounts.models.core`, `accounts.models.user`, `infrastructure.utils.pagination` | sqlalchemy | `User`,`Address`,`Cart`,`CartItem`,`UserSession`,`get_current_user`,`get_user_by_id`, referral helpers |
| [backend/domains/orders/ports.py](backend/domains/orders/ports.py#L548) | own + lazy catalog | `orders.models.*`; lazy `catalog.ports` | sqlalchemy | `Order`,`OrderItem`,`get_order_by_id`,`list_orders`,`create_coupon_from_payload`,`get_cart_shipping_quote` |
| [backend/domains/catalog/ports.py](backend/domains/catalog/ports.py) | own models | `catalog.models.products` | sqlalchemy | `Product`,`Category`,`Review`,`Wishlist(Item)`,`BOGOPromotion`,`resolve_product_variant`,`get_product_by_id` |
| comms/audit/finance/security/country/customers/suppliers/promotions `ports.py` | own models + pagination | intra-domain models | sqlalchemy | domain-scoped read helpers + re-exported models |

### Backend — representative domain models & services

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [backend/domains/accounts/models/user.py](backend/domains/accounts/models/user.py#L15-L23) | Base, catalog+customers models | `.`(Base), `infrastructure.utils.datetime_utils`, `domains.catalog.models.products`, `domains.customers.models.customer_schema_models` | sqlalchemy | `User`,`UserSession`,`UserLoginHistory`,`UserDevice`,`PasswordResetToken`,`EmailVerificationToken`,`RevokedToken` |
| [backend/domains/catalog/models/products.py](backend/domains/catalog/models/products.py#L1-L10) | Base only (string relationships) | `.`(Base), `infrastructure.utils.datetime_utils` | sqlalchemy | `Category`,`Product`,`ProductVariant`,`Review`,`WishlistItem`,`Wishlist`,`ProductVideo`,… (`__all__`) |
| [backend/domains/finance/services/payments/payment_engine.py](backend/domains/finance/services/payments/payment_engine.py#L8-L93) | finance models, config, providers | `domains.finance.models.finance`, `infrastructure.utils.config`, providers/payments (INFERRED) | sqlalchemy | payment engine + `_payment_provider_runtime_status` (used by `main.py:145`) |
| [backend/domains/orders/services/core/order_engine.py](backend/domains/orders/services/core/order_engine.py#L58-L61) | config, kernel.money | `infrastructure.utils.config`, `kernel.money` | sqlalchemy | order pricing/engine helpers |

### Backend — modules (role routers, top layer)

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [backend/modules/admin/routers/catalog.py](backend/modules/admin/routers/catalog.py#L34-L37) | DB dep + rbac gate + domain services | `infrastructure.database.database` (`get_db`), `rbac.dependencies` (`require_feature`), `domains.catalog.*` | fastapi | `router` (APIRouter) |
| modules/{admin,customer,employee,logistics,supplier}/routers/*.py (≈95 files) | `get_db` + `require_feature`/`get_current_user` + domain services/ports | `infrastructure.database.database`, `rbac.dependencies`, `domains.*` | fastapi | per-file `router` |

### Frontend — hubs (`frontend/web_app/src`)

| File | Key Imports | Internal Dependencies | External Dependencies | Exports |
|---|---|---|---|---|
| [frontend/web_app/src/lib/api/index.ts](frontend/web_app/src/lib/api/index.ts#L6-L9) | barrel | `./client`,`./auth`,`./errors`,`./country` | — | `apiFetch`,`API_URL`,`parseJsonResponse`,`getErrorMessage`,`setAccessToken`,`getAccessToken`,`clearAccessToken`,`detectCountryFromIP`,… |
| [frontend/web_app/src/lib/api/client.ts](frontend/web_app/src/lib/api/client.ts#L6-L18) | requestCache, auth, country | `@shared/requestCache`, `./auth`, `./country` | next runtime/env | `apiFetch`,`API_URL`,`DEFAULT_API_TIMEOUT_MS`,`parseJsonResponse`,`responseCache` |
| [frontend/web_app/src/lib/useAuth.tsx](frontend/web_app/src/lib/useAuth.tsx#L11-L22) | api + stores + shared | `@/lib/api`,`@/lib/localeStore`,`@/lib/cartStore`,`@/lib/authModalStore`,`@/lib/i18n`,`@shared/localization`,`@shared/adminPermissions` | react, next/navigation | `AuthProvider`,`useAuth`,`useRequireLogisticsPartner`,`UserInfo` |
| [frontend/web_app/src/app/layout.tsx](frontend/web_app/src/app/layout.tsx#L7) | AuthProvider | `@/lib/useAuth` + providers | react/next | root layout |

---

## HIGH-DEPENDENCY MODULES (imported by many)

1. **`infrastructure/database/database.py`** — **VERIFIED**, `HIGH`.
   339 import statements across 241 files (`grep "from infrastructure.database.database import"`).
   Consumers span every `modules/*/routers/*` (e.g. `backend/modules/admin/routers/accounts.py:43`,
   `backend/modules/customer/routers/orders.py:11`), most domain services
   (`backend/domains/orders/services/checkout/service.py:20`), all `jobs/*`
   (`backend/jobs/periodic_tasks.py:26`), and `main.py:26`. It is the single
   largest fan-in node. Imports only `infrastructure.utils.config` + `infrastructure.database.base`.

2. **`rbac/dependencies.py`** — **VERIFIED**, `HIGH`.
   252 matches across 110 files (`grep "from rbac"`), dominated by
   `from rbac.dependencies import require_feature` in ~95 router files across all 5 modules
   (`backend/modules/admin/routers/catalog.py:37`, `backend/modules/employee/routers/hr/leaves.py:9`,
   `backend/modules/supplier/routers/suppliers.py:10`). Every authorized endpoint depends on it.

3. **`infrastructure/utils/config.py` → `config.py`** — **VERIFIED**, `HIGH`.
   100 matches across 74 files (`grep "from infrastructure.utils.config import"`), all resolving
   to `settings`/`BASE_DIR` (`backend/main.py:29`, `backend/middleware/orchestrator.py:65`,
   `backend/jobs/celery_app.py:8`). Note THREE import paths collapse to one source
   (`backend/config.py`) via shims (`backend/infrastructure/utils/config.py:2`,
   `backend/infrastructure/config.py:7`).

4. **`domains/governance/ports.py`** — **VERIFIED**, `HIGH`.
   Imported by ~10 domains + modules for `User`, `archive_entity`, `restore_entity`,
   `hard_delete_entity`, `export_*` (e.g. `backend/domains/suppliers/services/supplier_shared.py:31`,
   `backend/domains/logistics/services/core/service.py:805`,
   `backend/domains/orders/services/admin_orders_service.py:10`,
   `backend/domains/security/services/fraud/fraud_detection_service.py:20`). See Hotspots §H1.

5. **`infrastructure/messaging/events/event_bus.py`** — **VERIFIED**, `MEDIUM`.
   54 matches across 28 files (`grep publish|subscribe|EventBus|publish_event`); every domain
   `events.py`/`subscribers.py` imports it (`backend/domains/orders/events.py:87`,
   `backend/domains/accounts/subscribers.py:12`). Central to write-side decoupling.

6. **`kernel/money.py`** — **VERIFIED**, `MEDIUM`.
   Dominant kernel consumer (`from kernel.money import round_money, to_decimal`) across finance,
   orders, promotions, logistics, catalog (`backend/domains/orders/services/core/order_engine.py:61`,
   `backend/domains/finance/services/ledger/general_ledger_service.py:13`,
   `backend/domains/logistics/services/partners/pricing_service.py:17`). Other kernel modules are
   comparatively rarely imported.

7. **Frontend `@/lib/api`** — **VERIFIED**, `HIGH`.
   `import { apiFetch, … } from "@/lib/api"` appears in 200+ files (combined api/useAuth/rbac scan =
   329 matches / 242 files; `@/lib/api` is the majority). It is the sole HTTP boundary
   (`frontend/web_app/src/app/products/page.tsx:12`, `.../components/admin/AdminChatPanel.tsx:15`).

8. **Frontend `@/lib/useAuth`** — **VERIFIED**, `HIGH`.
   `useAuth`/`AuthProvider` imported by layout + most authenticated pages/components
   (`frontend/web_app/src/app/layout.tsx:7`, `.../components/Header.tsx:28`,
   `.../app/checkout/page.tsx:17`).

---

## CIRCULAR DEPENDENCIES (confirmed chains only)

> **Skepticism note:** These are **package-level** cyclic import *edges* (domain A imports domain B
> AND domain B imports domain A), each edge proven at a real `file:line`. They are **not proven to be
> Python `ImportError` deadlocks**: the platform tolerates them at runtime via (a) the lifespan
> preloader importing every model module in a controlled pass (`backend/lifespan.py:21-22`,
> `_preload_all_models`), (b) SQLAlchemy **string-based** relationships so models needn't import each
> other's classes (`backend/domains/catalog/models/products.py:8`), and (c) `ports.py` importing
> sibling **models** (leaf-ish) rather than sibling **services**. I did NOT execute the loader, so the
> "no deadlock" outcome is INFERRED, while each edge is VERIFIED.

**C-CYC-1 accounts ↔ governance** — **VERIFIED**
- accounts→governance: `backend/domains/accounts/services/identity/identity_admin_service.py:19` (`from domains.governance.ports import User`); `backend/domains/accounts/services/users/user_management_service.py:25`; `backend/domains/accounts/services/auth/security_dependencies.py:171` (lazy).
- governance→accounts: `backend/domains/governance/ports.py:43-44` (`from domains.accounts.models.banking …`, `from domains.accounts.models.user …`); `backend/domains/governance/services/users_service.py:7`; `backend/domains/governance/subscribers.py:56` (lazy).

**C-CYC-2 accounts ↔ catalog** — **VERIFIED** (model-layer)
- accounts→catalog: `backend/domains/accounts/models/user.py:21` (`from domains.catalog.models.products import Product, Review, WishlistItem, Wishlist`) — top-level despite the "Lazy imports" comment (Contradiction C2).
- catalog→accounts: `backend/domains/catalog/services/admin_catalog_orders_service.py:5` (`from domains.accounts.ports import User`); `backend/domains/catalog/services/products/products_service.py:383` (lazy `from domains.accounts.ports import CartItem`).

**C-CYC-3 accounts ↔ customers** — **VERIFIED**
- accounts→customers: `backend/domains/accounts/models/user.py:22` (`from domains.customers.models.customer_schema_models import Referral`).
- customers→accounts: `backend/domains/customers/services/compliance_service.py:16` (`from domains.accounts.ports import Address, User, UserSession`); `backend/domains/customers/services/cart_service.py:23` (`from domains.accounts.models.core import CartItem`).

**C-CYC-4 catalog ↔ governance** — **VERIFIED**
- catalog→governance: `backend/domains/catalog/services/categories/admin_categories_service.py:23`; `backend/domains/catalog/services/products/admin_products_service.py:8`.
- governance→catalog: `backend/domains/governance/services/products_service.py:6` (`from domains.catalog.models.products import Product`).

**C-CYC-5 security ↔ governance** — **VERIFIED**
- security→governance: `backend/domains/security/services/fraud/fraud_detection_service.py:20` (`from domains.governance.ports import User, UserLoginHistory, UserDevice`); `backend/domains/security/services/iam/iam_service.py:15`.
- governance→security: `backend/domains/governance/ports.py:50` (`from domains.security.models.fraud import …`); `backend/domains/governance/models/fraud.py:4`.

**C-CYC-6 suppliers ↔ governance** — **VERIFIED**
- suppliers→governance: `backend/domains/suppliers/services/supplier_shared.py:31`; `backend/domains/suppliers/services/governance/admin_suppliers_service.py:15`.
- governance→suppliers: `backend/domains/governance/ports.py:45` (`from domains.suppliers.models.suppliers import SupplierDispute`).

**C-CYC-7 promotions ↔ governance** — **VERIFIED**
- promotions→governance: `backend/domains/promotions/services/coins/promotion_points_service.py:31`; `backend/domains/promotions/services/engine/promotion_engine_service.py:17`.
- governance→promotions: `backend/domains/governance/ports.py:46-48` (`from domains.promotions.models.coupon_usage/promotion_config/promotion_ledger …`).

**C-CYC-8 comms ↔ governance** — **VERIFIED**
- comms→governance: `backend/domains/comms/services/comms_service.py:30` (`from domains.governance.ports import User`).
- governance→comms: `backend/domains/governance/ports.py:51-52` (`from domains.comms.models.fraud`, `from domains.comms.models.incident`); `backend/domains/governance/services/admin/bulk_ops_service.py:9`.

**C-CYC-9 finance ↔ governance** — **VERIFIED**
- finance→governance: `backend/domains/finance/services/payouts/payout_batch_service.py:843` (`from domains.governance.ports import LogisticsSettlement`).
- governance→finance: `backend/domains/governance/services/misc_write_service.py:19` (`from domains.finance.ports import create_cash_account, create_cash_transaction`); `backend/domains/governance/services/command_center/background.py:706` (lazy).

**Intra-domain (single-domain) cycles** — INFERRED tolerated: e.g. `finance.services.__init__` star-imports
submodules (`backend/domains/finance/services/__init__.py:4`) that themselves import finance models; and
`governance.models.__init__` imports `governance.models.fraud` (`backend/domains/governance/models/__init__.py:2`)
which re-exports `security.models.fraud`. These are same-package or documented re-exports, not new cross edges.

**Sanctioned-debt register:** `backend/DOMAIN_ALLOWLIST.yaml:1-45` explicitly enumerates temporary
cross-domain edges (finance→comms/governance/logistics/suppliers, governance.models.fraud→security/comms),
confirming the team is aware these edges exist and intends them to "only shrink".

---

## ORPHAN MODULES (appear unreferenced — NOT asserted dead)

> "Orphaned" here = no first-party runtime import found by targeted `grep`. Reasons vary; none proven dead.

1. **`backend/domains/orders/serializers.py`** — **VERIFIED no refs found**, `LOW`.
   Zero matches for `orders.serializers` / `from domains.orders import serializers`. A parallel
   `backend/domains/orders/schemas/serializers.py` exists. WHY it appears orphaned: likely superseded by
   the `schemas/` variant during the DDD reshape; may still be re-exported via a star-import not captured,
   or genuinely stale. Needs Phase 13 confirmation before deletion.

2. **`backend/providers/async_workers.py`** — **VERIFIED refs = tests + self only**, `LOW`.
   Referenced only by its own test (`backend/tests/providers/test_news_analytics_automation_finance_base_providers.py:1203-1312`)
   and a self-referential docstring (`backend/providers/async_workers.py:12`). WHY: appears to be a
   provider utility retained for test coverage but not wired into runtime app code.

3. **`backend/providers/observability.py`** — **INFERRED legacy shim**, `LOW`.
   `backend/infrastructure/observability/provider_observability.py:7` states the "real implementation
   relocated from `providers.observability` (P13 root-leak…)". Still imported at
   `backend/domains/orders/services/returns/service.py:259` (lazy `capture_exception`) + tests, so it is
   NOT unreferenced — flagged as a **relocation remnant**, not an orphan.

4. **`backend/.kilo/*.py`** (`create_shims.py`, `update_imports*.py`, `extract_modules.py`, …) —
   **VERIFIED tooling**, `INFO`. One-off migration scripts; orphaned by design (not imported by app).

5. **`backend/domains/orders/customer_coupons_create_service.py`** (top-level) — **NOT orphan**.
   Imported by `backend/domains/promotions/services/coupons/customer_coupons_create_service.py:21`
   (`delete_coupon`). Listed to correct the superficial "duplicate ⇒ dead" assumption.

6. **`backend/scripts/_debug/*`** — **VERIFIED debug scripts**, `INFO`. Standalone diagnostics; not imported.

**Frontend:** No systematic orphan sweep performed (Next.js `app/` files are route-convention entrypoints,
so absence of an explicit import does NOT imply orphaning). NOT DETERMINABLE FROM AVAILABLE CODE without a
bundler-graph pass.

---

## ARCHITECTURAL HOTSPOTS (unusually high dependency concentration)

**H1 — `domains/governance/ports.py` is a cross-domain "god-facade".** **VERIFIED**, `HIGH`.
It imports models from **seven** sibling domains at module top level
(`backend/domains/governance/ports.py:42-52`: accounts, suppliers, promotions, customers, security, comms +
own) while being imported by ~10 domains and multiple modules. It therefore sits inside **five** of the
nine confirmed cycles (C-CYC-1,4,5,6,7,8,9). Why it matters: it is the single most likely trigger for
import-order fragility, and any change to a sibling domain's model surface ripples through governance into
every consumer. It concentrates both fan-in and fan-out.

**H2 — `infrastructure/database/database.py` fan-in (241 files).** **VERIFIED**, `HIGH`.
Any change to session/engine semantics (pooling, `get_db` contract, RLS hooks) touches the entire codebase.
It is correctly a low-layer leaf (only depends on config+base), so the risk is blast radius, not cycles.

**H3 — `rbac/dependencies.py` gate fan-in (~95 routers).** **VERIFIED**, `MEDIUM`.
Every authorized endpoint depends on `require_feature`; combined with `rbac.catalog` as the feature
single-source (`backend/rbac/dependencies.py:11`), the RBAC package is a chokepoint for authz correctness.
Internal chain: `catalog → dependencies → roles → service → resolution` (`backend/rbac/roles.py:11`,
`backend/rbac/service.py:13,135-136`).

**H4 — `middleware/orchestrator.py` aggregates 16 middleware.** **VERIFIED**, `MEDIUM`.
Single wiring point (`backend/middleware/orchestrator.py:46-63`) importing all middleware classes; ordering
is behavioral (documented layers 1–5). High coupling but intentional and localized.

**H5 — Frontend `@/lib/api` is the sole network boundary (200+ importers).** **VERIFIED**, `HIGH`.
`frontend/web_app/src/lib/api/index.ts:6-9` barrels `client/auth/errors/country`. Every data-fetching page
and component funnels through `apiFetch`. Concentrated fan-in; also a natural place where a bug affects the
whole app. `@/lib/useAuth` is a secondary hub layered on top of it (`frontend/web_app/src/lib/useAuth.tsx:12`).

**H6 — Config triple-aliasing.** **VERIFIED**, `MEDIUM`.
`settings` is reachable via `config`, `infrastructure.utils.config`, and `infrastructure.config`
(`backend/infrastructure/utils/config.py:2`, `backend/infrastructure/config.py:7`). Three import surfaces
for one source increases the chance of inconsistent references and complicates dependency reasoning.

---

## CONTRADICTIONS (rules 10–11: reported, not silently resolved)

- **C1 — models.py comment vs behavior.** `backend/main.py:11-12` imports
  `from infrastructure.database import models` with comment "registers all ORM models", but
  `backend/infrastructure/database/models.py:11-16` only calls `clear_mappers()` and imports **no** domain
  models (registration is delegated to the lifespan preloader per its own docstring
  `backend/infrastructure/database/models.py:1-9`). **VERIFIED.**
- **C2 — "Lazy imports" that are eager.** `backend/domains/accounts/models/user.py:20` comment says
  "Lazy imports for cross-domain relationships (avoid circular imports)", but lines 21-22 are ordinary
  top-level (eager) imports of `catalog` and `customers` models. **VERIFIED.**
- **C3 — Enforced law vs live edges.** `backend/tests/_support/laws.py:60-70` forbids `domains → modules`
  and the diagram mandates cross-domain reads via `ports.py`, yet `DOMAIN_ALLOWLIST.yaml:24-31` sanctions
  live `domains.finance.services.* → modules.admin.routers.auth` and fastapi-in-service imports. The
  allowlist is the escape hatch; reported as an acknowledged rule/implementation gap. **VERIFIED.**

---

## Positive structural findings (evidence)

- **Providers layer is clean.** `grep "^from (domains|modules|rbac|jobs|middleware)" backend/providers/**`
  returned **0 matches** → the provider layer never imports upward, satisfying its rule
  (`backend/tests/_support/laws.py:66`). **VERIFIED.**
- **Event-bus decoupling is real and uniform.** All 16 domains carry `events.py`+`subscribers.py`
  importing `event_bus.publish/subscribe` (`backend/domains/*/events.py`, `.../subscribers.py`;
  scan = 54 matches/28 files). This is the sanctioned cycle-breaker for writes
  (`backend/infrastructure/messaging/events/event_bus.py:1-10`). **VERIFIED.**

---

## Gaps / NOT DETERMINABLE

- Whether any package-level cycle would raise a real Python `ImportError` at cold start — requires executing
  `_preload_all_models` (`backend/lifespan.py`) with the production import order. **NOT DETERMINABLE** statically.
- Frontend true dead-code/orphans — Next.js `app/` route files are convention-loaded; needs a bundler graph.
- `rbac/catalog.py` exact feature-file dependency set (it scans `domains/*/features.py`) — **INFERRED** from
  `backend/tests/_support/laws.py:74-79`; not line-traced here.
```
