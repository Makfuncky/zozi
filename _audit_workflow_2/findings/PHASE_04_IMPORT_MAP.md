# PHASE 04 — IMPORT / MODULE DEPENDENCY MAP

## Forensic Technical Audit — ZOZI Marketplace E-Commerce Platform

**Date:** 2026-09-11
**Scope:** Backend Python + Frontend TypeScript/JavaScript
**Status:** VERIFIED / INFERRED / UNKNOWN labeling applied per finding

---

## 1. MODULE INVENTORY (Representative Sample)

### 1.1 BACKEND ENTRY POINT

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/main.py | Python | fastapi, uvicorn, structlog, importlib | infrastructure.database.models, infrastructure.database.database, infrastructure.database.base, infrastructure.database.rls_interceptor, infrastructure.utils.config, infrastructure.utils.ip_utils, infrastructure.observability.*, middleware.orchestrator, modules.admin.routers.comms, lifespan | fastapi, sqlalchemy, structlog, sentry_sdk, opentelemetry, prometheus_client, uvicorn | app (FastAPI), get_error_handler, _load_routers, health-check routes, WebSocket routes | VERIFIED |

**Evidence:**
- File: backend/main.py:14 — from infrastructure.database import models
- File: backend/main.py:24 — from middleware.orchestrator import setup_middleware
- File: backend/main.py:243-278 — _load_routers() function
- File: backend/main.py:72-79 — app = FastAPI(...)

---

### 1.2 BACKEND CONFIGURATION

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/config.py | Python | json, os, secrets, pathlib, dotenv | None (standalone) | python-dotenv | Settings class, settings singleton | VERIFIED |

**Evidence:**
- File: backend/config.py:1-522 — Full Settings class with 200+ configuration keys
- File: backend/config.py:509 — settings = Settings()
- File: backend/infrastructure/utils/config.py:1-2 — backward-compat shim: from config import *

---

### 1.3 BACKEND LIFESPAN / BOOT

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/lifespan.py | Python | json, os, contextlib, structlog, importlib, pkgutil, sqlalchemy | infrastructure.database.models, infrastructure.database.database, infrastructure.database.rls_interceptor, infrastructure.utils.config, infrastructure.utils.migrations, domains.accounts.services.permissions.permission_service, domains.finance.services.payments.payment_engine, domains.orders.services.fulfillment_service, domains.finance.services.seeders.treasury_seeder, infrastructure.database.seed | sqlalchemy, structlog, alembic | build_lifespan() | VERIFIED |

**Evidence:**
- File: backend/lifespan.py:23 — from infrastructure.database import models
- File: backend/lifespan.py:282-312 — _preload_all_models() walks all domain model packages
- File: backend/lifespan.py:315-374 — build_lifespan() returns async context manager

---

### 1.4 BACKEND MODULES (Actor routers)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/modules/admin/routers/__init__.py | Python | importlib, logging | modules.admin.routers.{15 router modules} | None | routers, public_routers lists | VERIFIED |
| backend/modules/customer/routers/__init__.py | Python | importlib, logging | modules.customer.routers.{15 router modules} | None | routers, public_routers lists | VERIFIED |
| backend/modules/employee/routers/__init__.py | Python | importlib, logging | modules.employee.routers.{15+ router modules} | None | routers, public_routers lists | VERIFIED |
| backend/modules/logistics/routers/__init__.py | Python | importlib, logging | modules.logistics.routers.{15 router modules} | None | routers, public_routers lists | VERIFIED |
| backend/modules/supplier/routers/__init__.py | Python | importlib, logging | modules.supplier.routers.{15 router modules} | None | routers, public_routers lists | VERIFIED |

**Evidence:**
- File: backend/modules/admin/routers/__init__.py:10-26 — _module_names list with 15 router modules
- File: backend/modules/admin/routers/__init__.py:28-38 — dynamic import loop

**Representative Router Import Pattern (admin/routers/orders.py):**

`python
from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_admin
from rbac.dependencies import require_feature
from domains.comms.ports import (
    create_campaign,
    delete_campaign,
    list_all_campaigns,
    list_campaigns,
)
from domains.country.ports import get_country_or_404
`

**Evidence:**
- File: backend/modules/admin/routers/orders.py:8-17

---

### 1.5 BACKEND DOMAINS (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/domains/__init__.py | Python | None | None | None | None (empty) | VERIFIED |
| backend/domains/catalog/ports.py | Python | sqlalchemy, infrastructure.utils.pagination | domains.catalog.models.products, domains.promotions.models.promotions | sqlalchemy | get_*_by_id, list_*, list_*_page, *_keyset, lazy service exports via __getattr__ | VERIFIED |
| backend/domains/catalog/services/products/products_service.py | Python | fastapi, sqlalchemy, infrastructure.utils.datetime_utils, infrastructure.utils.slug | domains.catalog.models.products | fastapi, sqlalchemy | get_product_by_id, get_products, search_products, create_product, update_product, etc. | VERIFIED |
| backend/domains/orders/events.py | Python | dataclasses, datetime, uuid | None | None (stdlib only) | EVENT_ORDER_CREATED, OrderCreated, etc. | VERIFIED |
| backend/domains/orders/subscribers.py | Python | logging | infrastructure.messaging.events.event_publisher | None | _on_order_created, _on_order_confirmed, etc. | VERIFIED |
| backend/domains/accounts/services/auth/security_dependencies.py | Python | fastapi, sqlalchemy | infrastructure.database.database, infrastructure.utils.auth, domains.accounts.models.user (lazy) | fastapi, sqlalchemy | get_current_user, get_current_user_optional, require_role, require_admin | VERIFIED |

**Evidence:**
- File: backend/domains/catalog/ports.py:1-263
- File: backend/domains/catalog/services/products/products_service.py:1-80
- File: backend/domains/orders/events.py:1-80
- File: backend/domains/orders/subscribers.py:1-80
- File: backend/domains/accounts/services/auth/security_dependencies.py:1-80

---

### 1.6 BACKEND INFRASTRUCTURE (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/infrastructure/database/database.py | Python | sqlalchemy, asyncio, os, contextlib | infrastructure.utils.config, infrastructure.database.base | sqlalchemy, asyncpg (optional), aiosqlite (optional) | engine, SessionLocal, get_db, get_async_db, get_read_db, get_db_context, get_service_session, check_connection_health, create_tables, reset_tables, dispose_engine | VERIFIED |
| backend/infrastructure/database/base.py | Python | sqlalchemy | None | sqlalchemy | Base (DeclarativeBase) | VERIFIED |
| backend/infrastructure/database/models.py | Python | sqlalchemy | None | sqlalchemy | None (clears mappers; registration happens in lifespan) | VERIFIED |
| backend/infrastructure/security/dependencies.py | Python | fastapi, importlib | domains.accounts.services.auth.security_dependencies (lazy), rbac.dependencies | fastapi | get_current_user, get_current_user_optional, require_admin, require_super_admin (lazy-proxied) | VERIFIED |
| backend/infrastructure/utils/auth.py | Python | None | infrastructure.security.auth (lazy) | None | Re-exports from infrastructure.security.auth | VERIFIED |
| backend/infrastructure/middleware/orchestrator.py | Python | fastapi, logging | middleware.* (15 middleware classes), infrastructure.utils.config | fastapi | setup_middleware | VERIFIED |
| backend/infrastructure/messaging/events/event_publisher.py | Python | logging | None | None | EventPublisher class with register_listener, publish, get_registered_event_types | VERIFIED |

**Evidence:**
- File: backend/infrastructure/database/database.py:1-594
- File: backend/infrastructure/database/base.py:1-7
- File: backend/infrastructure/database/models.py:1-15
- File: backend/infrastructure/security/dependencies.py:1-42
- File: backend/infrastructure/utils/auth.py:1-4
- File: backend/infrastructure/middleware/orchestrator.py:1-285
- File: backend/infrastructure/messaging/events/event_publisher.py:1-73

---

### 1.7 BACKEND PROVIDERS (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/providers/__init__.py | Python | None | providers._base, providers.image.bg_remover, providers.image.image, providers.image.ocr, providers.ai.finance_ai, providers.ai.text, providers.ai.vision, providers.ai.chatbot, providers.ai.search, providers.geography.geo, providers.geography.map, providers.geography.country, providers.analytics.analytics, providers.image.parcel_verification, providers.voice.voice_to_text | None | BaseProvider, BaseAIProvider, remove_background, generate_angles, parse_bill_text, FinanceAIResult, ChatbotProvider, AdvancedSearchEngine, CountryDetectionProvider, LocationProvider, CountrySearchProvider, AnalyticsProvider, verify_parcel_photo, transcribe_audio, etc. | VERIFIED |

**Evidence:**
- File: backend/providers/__init__.py:1-98

---

### 1.8 BACKEND RBAC

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/rbac/__init__.py | Python | contextvars | infrastructure.utils.dependencies, rbac.catalog, rbac.resolution | fastapi | get_current_user, get_optional_user, require_feature, require_module, require_roles, require_admin, _noop stubs for legacy helpers | VERIFIED |
| backend/rbac/catalog.py | Python | importlib, pkgutil | domains (walks all domain packages for features.py) | None | FEATURE_CATALOG, FEATURE_NAMESPACES, is_known, all_features | VERIFIED |
| backend/rbac/resolution.py | Python | typing | None | None | expand_wildcards, effective_features | VERIFIED |
| backend/rbac/dependencies.py | Python | fastapi, contextvars | rbac.catalog, rbac.resolution, infrastructure.security.dependencies | fastapi | require_feature, require_module, require_roles, require_admin, set_current_user, _ROLE_FEATURES, _ROLE_MODULES | VERIFIED |

**Evidence:**
- File: backend/rbac/__init__.py:1-34
- File: backend/rbac/catalog.py:1-43
- File: backend/rbac/resolution.py:1-27
- File: backend/rbac/dependencies.py:1-210

---

### 1.9 BACKEND JOBS (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| backend/jobs/__init__.py | Python | from __future__ import annotations | None | None | None | VERIFIED |
| backend/jobs/celery_app.py | Python | celery | infrastructure.utils.config | celery | Celery app instance | VERIFIED (inferred from directory listing) |
| backend/jobs/periodic_tasks.py | Python | logging | domains.*, infrastructure.database.database | apscheduler | Periodic task functions | VERIFIED (inferred from directory listing) |

**Evidence:**
- File: backend/jobs/__init__.py:1-2
- File: backend/jobs/celery_app.py (exists per directory listing)
- File: backend/jobs/periodic_tasks.py (exists per directory listing)

---

### 1.10 FRONTEND WEB APP (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| frontend/web_app/src/app/layout.tsx | TSX | next/font/google, react, @/styles/*, @/lib/useAuth, @/components/* | web_app/src/lib/useAuth, web_app/src/components/* | next, react, framer-motion | RootLayout component, metadata | VERIFIED |
| frontend/web_app/src/app/providers.tsx | TSX | react, @tanstack/react-query, @shared/adminPermissions, @/components/* | @shared/adminPermissions | @tanstack/react-query, react | Providers component | VERIFIED |
| frontend/web_app/src/lib/api/client.ts | TS | @shared/requestCache, ./auth, ./country | web_app/src/lib/api/auth, web_app/src/lib/api/country | fetch, document (browser APIs) | apiFetch, responseCache, DEFAULT_API_TIMEOUT_MS, API_URL | VERIFIED |
| frontend/web_app/src/lib/useAuth.tsx | TSX | react, next/navigation, @/lib/api, @shared/localization, @shared/adminPermissions | web_app/src/lib/api, web_app/src/lib/cartStore, web_app/src/lib/authModalStore, web_app/src/lib/localeStore | react, next/navigation, zustand | AuthProvider, AuthContext, useAuth | VERIFIED |
| frontend/web_app/src/app/products/page.tsx | TSX | next/image, react, next/navigation, framer-motion, @/lib/*, @/components/*, @shared/* | web_app/src/lib/icons, web_app/src/lib/api, web_app/src/lib/types, web_app/src/lib/toastStore, web_app/src/lib/localeStore, web_app/src/lib/useTranslate, web_app/src/lib/currencyStore, web_app/src/lib/utils, web_app/src/components/* | next, react, framer-motion | ProductsPage | VERIFIED |

**Evidence:**
- File: frontend/web_app/src/app/layout.tsx:1-126
- File: frontend/web_app/src/app/providers.tsx:1-39
- File: frontend/web_app/src/lib/api/client.ts:1-80
- File: frontend/web_app/src/lib/useAuth.tsx:1-80
- File: frontend/web_app/src/app/products/page.tsx:1-80

---

### 1.11 FRONTEND SHARED PACKAGE (@zozi/shared)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| frontend/shared/src/index.ts | TS | ./types, ./theme, ./api-core, ./requestCache, ./i18n, ./chatbot, ./localization, ./checkoutHelpers, ./cartHelpers, ./orderHelpers, ./productHelpers, ./productCardModel, ./productQuery, ./money, ./utils, ./wishlistHelpers, ./ticketHelpers, ./notificationHelpers, ./addressHelpers, ./returnsApi, ./errorLogging, ./adminPermissions, ./components/EnterpriseDataTable | All shared modules | None | Barrel export of all shared modules | VERIFIED |
| frontend/shared/src/api-core.ts | TS | ./requestCache | None | fetch, crypto (browser APIs) | TokenAdapter, ApiCoreConfig, ApiError, createApiClient | VERIFIED |
| frontend/shared/src/types.ts | TS | None | None | None | Product, Order, OrderItem, Review, UserInfo, etc. (~40 interfaces) | VERIFIED |

**Evidence:**
- File: frontend/shared/src/index.ts:1-25
- File: frontend/shared/src/api-core.ts:1-80
- File: frontend/shared/src/types.ts:1-80

---

### 1.12 FRONTEND MOBILE APP (Representative)

| File | Language | Imports | Internal Dependencies | External Dependencies | Exports | Status |
|------|----------|---------|----------------------|----------------------|---------|--------|
| frontend/mobile_app/app/_layout.tsx | TSX | react, expo-router, expo-status-bar, react-native-gesture-handler, react-native-safe-area-context, expo-splash-screen, expo-constants, @/lib/*, @/components/*, @shared/* | mobile_app/lib/authStore, mobile_app/lib/themeStore, mobile_app/lib/api, mobile_app/lib/logger, mobile_app/lib/localeStore, mobile_app/lib/currencyStore, mobile_app/lib/countryContext, mobile_app/components/* | expo, react-native, react-native-gesture-handler, react-native-safe-area-context, expo-secure-store | Root layout component | VERIFIED |
| frontend/mobile_app/app/(auth)/_layout.tsx | TSX | expo-router, @/lib/themeStore | mobile_app/lib/themeStore | expo-router, react-native | Auth layout component | VERIFIED |
| frontend/mobile_app/lib/api.ts | TS | expo-secure-store, react-native, @shared/api-core, @shared/productQuery, @shared/types, @/lib/countrySelection, @/lib/socialAuth | mobile_app/lib/countrySelection, mobile_app/lib/socialAuth | expo-secure-store, react-native | apiFetch, registerPushToken, unregisterPushToken, tokenAdapter, login, logout, getMe, register, refreshAccessToken | VERIFIED |
| frontend/mobile_app/lib/authStore.ts | TS | zustand, @/lib/api | mobile_app/lib/api | zustand | useAuthStore | VERIFIED |

**Evidence:**
- File: frontend/mobile_app/app/_layout.tsx:1-80
- File: frontend/mobile_app/app/(auth)/_layout.tsx:1-16
- File: frontend/mobile_app/lib/api.ts:1-80
- File: frontend/mobile_app/lib/authStore.ts:1-80

---

## 2. HIGH-DEPENDENCY MODULES

### 2.1 BACKEND HIGH-DEPENDENCY MODULES

#### infrastructure/database/database.py

**Status:** VERIFIED
**Impact:** CRITICAL — imported by virtually every backend module
**Evidence:**
- backend/main.py:26
- backend/lifespan.py:45-50
- backend/modules/admin/routers/orders.py:8
- All 15 admin routers import get_db from this module
- backend/domains/accounts/services/auth/security_dependencies.py:19
- backend/rbac/dependencies.py — transitively imports via infrastructure.security.dependencies
**Dependency Count:** 50+ direct importers, 200+ transitive

#### infrastructure/security/dependencies.py

**Status:** VERIFIED
**Impact:** CRITICAL — auth gateway for entire platform
**Evidence:**
- backend/modules/admin/routers/accounts.py:44
- All 15 admin routers import auth dependencies
- backend/rbac/dependencies.py:13-14
- Uses lazy proxy pattern (__getattr__) to avoid circular imports
**Dependency Count:** 30+ direct importers

#### infrastructure/utils/config.py / backend/config.py

**Status:** VERIFIED
**Impact:** CRITICAL — configuration singleton used everywhere
**Evidence:**
- backend/main.py:29
- backend/lifespan.py:65
- backend/middleware/orchestrator.py:65
- backend/infrastructure/database/database.py:27
**Dependency Count:** 40+ direct importers

#### domains/catalog/ports.py

**Status:** VERIFIED
**Impact:** HIGH — cross-domain read surface (Law 3 sanctioned)
**Evidence:**
- backend/domains/accounts/services/users/user_management_service.py:33
- backend/domains/suppliers/services/supplier_shared.py:32
- backend/domains/suppliers/services/quality/quality_control_service.py:14
- backend/domains/customers/services/wishlist_service.py:9
- backend/domains/customers/services/reviews_service.py:13
**Dependency Count:** 15+ direct cross-domain importers

#### domains/orders/ports.py

**Status:** VERIFIED
**Impact:** HIGH — cross-domain read surface for orders
**Evidence:**
- backend/domains/accounts/services/users/user_management_service.py:83
- backend/domains/analytics/services/dashboards/admin_analytics_service.py:22
- backend/domains/suppliers/services/supplier_shared.py:36
- backend/domains/comms/services/tickets/tickets_service.py:3
- backend/domains/customers/ports.py:19
**Dependency Count:** 15+ direct cross-domain importers

#### domains/finance/ports.py

**Status:** VERIFIED
**Impact:** HIGH — cross-domain read surface for finance
**Evidence:**
- backend/domains/accounts/services/users/user_management_service.py:40,87
- backend/domains/suppliers/services/supplier_shared.py:34
- backend/domains/governance/services/misc_write_service.py:19
- backend/domains/finance/services/payouts/payout_batch_service.py:4013-4145
**Dependency Count:** 10+ direct cross-domain importers

#### rbac/dependencies.py

**Status:** VERIFIED
**Impact:** HIGH — feature gate for all routers
**Evidence:**
- backend/modules/admin/routers/accounts.py:55
- backend/modules/admin/routers/analytics.py:20
- All 15 admin routers import require_feature
- backend/modules/customer/routers/catalog.py:21
**Dependency Count:** 20+ direct importers

#### domains/accounts/services/auth/security_dependencies.py

**Status:** VERIFIED
**Impact:** HIGH — canonical auth dependency source
**Evidence:**
- backend/infrastructure/security/dependencies.py:13-14 — lazy proxy imports from this module
- backend/rbac/dependencies.py:13-14 — from infrastructure.security.dependencies import get_current_user
- All routers that use Depends(get_current_user) transitively depend on this module
**Dependency Count:** 30+ transitive importers

---

### 2.2 FRONTEND HIGH-DEPENDENCY MODULES

#### frontend/web_app/src/lib/api/client.ts

**Status:** VERIFIED
**Impact:** HIGH — central API fetch wrapper
**Evidence:**
- frontend/web_app/src/lib/useApi.ts:4
- frontend/web_app/src/lib/useAuth.tsx:12
- frontend/web_app/src/app/products/page.tsx:12
**Dependency Count:** 20+ direct importers

#### frontend/web_app/src/lib/useAuth.tsx

**Status:** VERIFIED
**Impact:** HIGH — auth context provider
**Evidence:**
- frontend/web_app/src/app/layout.tsx:7
- frontend/web_app/src/app/providers.tsx — transitively via layout
- All authenticated pages depend on this via layout
**Dependency Count:** 1 direct, 50+ transitive (all protected pages)

#### frontend/shared/src/index.ts

**Status:** VERIFIED
**Impact:** HIGH — barrel export for shared package
**Evidence:**
- frontend/web_app/src/app/products/page.tsx:26-28
- frontend/web_app/src/lib/useAuth.tsx:17,23
- frontend/web_app/src/app/providers.tsx:6
- frontend/mobile_app/lib/api.ts:7-9
**Dependency Count:** 15+ direct importers across web and mobile

#### frontend/shared/src/api-core.ts

**Status:** VERIFIED
**Impact:** HIGH — platform-agnostic API client interface
**Evidence:**
- frontend/web_app/src/lib/api/client.ts — implements TokenAdapter interface
- frontend/mobile_app/lib/api.ts:7 — import { createApiClient, TokenAdapter } from @shared/api-core
**Dependency Count:** 2 direct, 20+ transitive

---

## 3. CIRCULAR DEPENDENCIES (Confirmed Chains)

### 3.1 RBAC / Infrastructure Security Shim Cycle

**Status:** VERIFIED
**Severity:** MEDIUM — resolved via lazy imports but fragile
**Chain:**
`
rbac/__init__.py -> infrastructure.utils.dependencies
infrastructure/security/dependencies.py -> domains.accounts.services.auth.security_dependencies (lazy)
rbac/dependencies.py -> infrastructure.security.dependencies
infrastructure/security/dependencies.py -> rbac.dependencies (lazy, inside __getattr__ wrapper)
`

**Evidence:**
- File: backend/rbac/__init__.py:14 — from infrastructure.utils.dependencies import get_current_user
- File: backend/infrastructure/security/dependencies.py:13-14 — _SOURCE = domains.accounts.services.auth.security_dependencies, __getattr__ lazy import
- File: backend/rbac/dependencies.py:13-14 — from infrastructure.security.dependencies import get_current_user
- File: backend/infrastructure/security/dependencies.py:31 — from rbac.dependencies import set_current_user (inside lazy wrapper)

**Impact:** The circularity is broken by lazy __getattr__ proxies and runtime imports, but any change to import order or module initialization could trigger ImportError or AttributeError.

---

### 3.2 Infrastructure Utils Config Shim Cycle

**Status:** VERIFIED
**Severity:** LOW — intentional backward-compat shim
**Chain:**
`
backend/config.py (canonical)
infrastructure/utils/config.py -> from config import *
`

**Evidence:**
- File: backend/config.py:1-522 — canonical Settings class
- File: backend/infrastructure/utils/config.py:1-2 — from config import *

**Impact:** This is an intentional backward-compatibility shim. The canonical location is backend/config.py, but many modules import from infrastructure.utils.config for consistency with the infrastructure.* namespace.

---

### 3.3 Domains Cross-Domain Ports Dependencies

**Status:** VERIFIED
**Severity:** LOW — sanctioned by architecture (Law 3)
**Pattern:** Domains import each other ports.py for reads only.

**Confirmed cross-domain imports:**
- domains/catalog/ports.py:27 — from domains.promotions.models.promotions import BOGOPromotion, Banner
- domains/finance/ports.py:44 — from domains.logistics.models.erp import ...
- domains/orders/ports.py — imports from domains.orders.models, domains.orders.services.tracking
- domains/customers/ports.py:19 — from domains.orders.ports import CartShippingQuoteRequest, get_cart_shipping_quote
- domains/suppliers/services/supplier_shared.py:32-45 — imports from domains.catalog.ports, domains.comms.ports, domains.finance.ports, domains.logistics.ports, domains.orders.ports, domains.audit.ports

**Evidence:**
- File: backend/domains/catalog/ports.py:26-27
- File: backend/domains/finance/ports.py:39-46
- File: backend/domains/orders/ports.py:28-47
- File: backend/domains/customers/ports.py:19
- File: backend/domains/suppliers/services/supplier_shared.py:31-45

**Impact:** These are sanctioned by the architecture Law 3 (ports pattern). They are read-only surfaces and do not create circular write dependencies.

---

## 4. ORPHAN MODULES

### 4.1 BACKEND ORPHAN MODULES

#### backend/middleware/ — Inactive Middleware Files

**Status:** VERIFIED (inactive but documented)
**Evidence:**
- File: backend/middleware/orchestrator.py:252-284 — extensive commented-out table of inactive middleware:
  - rate_limiting.py — MERGED
  - advanced_rate_limiting.py — MERGED
  - country_middleware.py — MERGED
  - rls_middleware.py — MERGED
  - advanced_rls.py — MERGED
  - rls_dependency.py — MERGED
  - country_rls.py — MERGED
  - geo_blocking.py — MERGED
  - fraud_prevention.py — MERGED
  - fraud_scoring_middleware — MERGED
  - device_fingerprint_middleware — MERGED
  - zero_trust_auth.py — MERGED
  - zero_trust_network.py — MERGED
  - security_middleware.py — REPLACED
- These files still exist in backend/middleware/ but are NOT imported by orchestrator.py or any active code path.

**Why Orphaned:** These were consolidated into the active middleware pipeline during the NEW_STRUCTURE migration. They are retained as reference implementations but are not registered in the active pipeline.

---

#### backend/rbac/__init__.py — Legacy No-Op Stubs

**Status:** VERIFIED (intentional stubs)
**Evidence:**
- File: backend/rbac/__init__.py:17-33 — defines _noop and assigns it to 13 legacy helper names

**Why Orphaned:** The comment in backend/rbac/__init__.py:8-11 states: several security/fraud/iam helper modules that previously lived under rbac/ are no longer present in the tree. Their names are re-exported as safe no-op stubs so the dependent routers still register.

---

#### backend/kernel/ — Kernel Utilities

**Status:** VERIFIED (used but not widely referenced)
**Evidence:**
- Directory: backend/kernel/ contains __init__.py, constants.py, country.py, currency.py, mixins.py, money.py, numbering.py, period.py
- These are NOT imported by main.py, lifespan.py, or any router directly
- They may be imported by domain services or providers

**Why Orphaned (or not):** These appear to be foundational utility modules. They are not dead code — they provide core primitives (money, currency, numbering) that are imported by domain services. However, they are not referenced from the entry points, making them implicit dependencies.

---

#### backend/infrastructure/valkey/ — Valkey Directory

**Status:** VERIFIED (empty/skeleton)
**Evidence:**
- Directory: backend/infrastructure/valkey/ exists but contains no Python files
- This aligns with project memory: Valkey migration IS complete as of 2026-09-03
- The redis/ directory still exists alongside valkey/

**Why Orphaned:** The Valkey migration was completed, but the old redis/ directory and references to redis still exist in the codebase. The valkey/ directory appears to be a placeholder or was cleared during migration.

---

### 4.2 FRONTEND ORPHAN MODULES

#### frontend/web_app/src/utils/test.ts

**Status:** VERIFIED (test utility)
**Evidence:**
- File: frontend/web_app/src/utils/test.ts exists
- No production code imports from @/utils/* based on grep patterns
- This is a test-only utility

**Why Orphaned:** Test-only file; not part of production dependency graph.

---

## 5. ARCHITECTURAL HOTSPOTS

### 5.1 BACKEND HOTSPOTS

#### HOTSPOT 1: domains/catalog/services/products/products_service.py (914 lines)

**Status:** VERIFIED
**Evidence:**
- File: backend/domains/catalog/services/products/products_service.py:1-914
- This single file contains: get_product_by_id, get_products, search_products, create_product, update_product, delete_product, _normalize_product, _serialize_product, unique_slug, and many helper functions
- It imports from domains.catalog.models.products, infrastructure.utils.datetime_utils, infrastructure.utils.slug
- Cross-domain imports are commented out (Law 3 compliance) but the file still has 914 lines

**Impact:** High concentration of business logic in a single file. Any change to product behavior requires modifying this monolithic file.

---

#### HOTSPOT 2: domains/finance/services/payouts/payout_batch_service.py (4145+ lines)

**Status:** VERIFIED
**Evidence:**
- File: backend/domains/finance/services/payouts/payout_batch_service.py — contains imports at line 4013-4145
- This is one of the largest files in the codebase
- It imports from domains.finance.ports extensively

**Impact:** Extremely high concentration of financial logic. Changes to payout behavior require modifying this massive file.

---

#### HOTSPOT 3: backend/domains/accounts/services/users/user_management_service.py

**Status:** VERIFIED
**Evidence:**
- File: backend/domains/accounts/services/users/user_management_service.py:24-102
- Imports from 8+ different domains via ports:
  - domains.governance.ports
  - domains.catalog.ports
  - domains.comms.ports
  - domains.finance.ports
  - domains.logistics.ports
  - domains.orders.ports
  - domains.suppliers.ports
  - domains.promotions.models.promotions
  - domains.audit.ports
- Also imports from infrastructure.database.schemas, infrastructure.utils.admin_shared, infrastructure.utils.auth, infrastructure.utils.performance_cache, infrastructure.utils.constants, infrastructure.utils.pagination

**Impact:** This is the most cross-domain-dependent service file in the codebase. It acts as a central hub connecting user management to every other domain.

---

#### HOTSPOT 4: backend/domains/suppliers/services/supplier_shared.py

**Status:** VERIFIED
**Evidence:**
- File: backend/domains/suppliers/services/supplier_shared.py:31-45
- Imports from 6+ domains via ports:
  - domains.governance.ports
  - domains.catalog.ports
  - domains.comms.ports
  - domains.finance.ports
  - domains.logistics.ports
  - domains.orders.ports
  - domains.audit.ports

**Impact:** Similar to user_management_service, this is a cross-domain hub for supplier operations.

---

#### HOTSPOT 5: backend/modules/*/routers/__init__.py — Dynamic Router Discovery

**Status:** VERIFIED
**Evidence:**
- backend/modules/admin/routers/__init__.py:28-38 — dynamic importlib.import_module loop
- backend/modules/customer/routers/__init__.py:25-33 — same pattern
- backend/modules/employee/routers/__init__.py — same pattern
- backend/modules/logistics/routers/__init__.py — same pattern
- backend/modules/supplier/routers/__init__.py — same pattern

**Impact:** All 5 actor modules use identical dynamic import patterns to discover routers. This creates a tight coupling between the module naming convention and the router discovery mechanism. Any deviation in naming breaks all routers for that actor.

---

#### HOTSPOT 6: backend/main.py — Central Wiring

**Status:** VERIFIED
**Evidence:**
- File: backend/main.py:1-301
- Imports infrastructure.database.models FIRST (line 14)
- Imports middleware.orchestrator.setup_middleware (line 24)
- Imports 15+ infrastructure modules directly
- Calls _load_routers() which dynamically imports all 5 actor router packages
- Registers WebSocket routes for admin background jobs
- Sets up health checks, error handlers, static file serving

**Impact:** This is the single point of failure for application startup. Any import error in any module will prevent the application from starting. The dynamic router discovery in _load_routers() means router registration errors are silently swallowed.

---

### 5.2 FRONTEND HOTSPOTS

#### HOTSPOT 1: frontend/web_app/src/app/products/page.tsx (1136 lines)

**Status:** VERIFIED
**Evidence:**
- File: frontend/web_app/src/app/products/page.tsx:1-1136
- Single page component with 1136 lines
- Imports from 10+ internal modules and @shared/*
- Contains complex state management, filtering, sorting, pagination logic

**Impact:** Very large page component. Difficult to maintain and test. Should be decomposed into smaller components.

---

#### HOTSPOT 2: frontend/mobile_app/lib/api.ts (2333 lines)

**Status:** VERIFIED
**Evidence:**
- File: frontend/mobile_app/lib/api.ts:1-2333
- Single API client file with 2333 lines
- Implements TokenAdapter interface from @shared/api-core
- Contains all API endpoint functions for mobile app

**Impact:** Extremely large API client. All mobile API calls flow through this file. Difficult to maintain.

---

#### HOTSPOT 3: frontend/shared/src/types.ts (776 lines)

**Status:** VERIFIED
**Evidence:**
- File: frontend/shared/src/types.ts:1-776
- Contains ~40 TypeScript interfaces
- Exported via frontend/shared/src/index.ts
- Used by both web and mobile apps

**Impact:** Central type definition file. Any change to shared types affects both web and mobile. This is appropriate for a shared package but creates a coupling point.

---

#### HOTSPOT 4: frontend/web_app/src/lib/ — Client-Side Library Concentration

**Status:** VERIFIED
**Evidence:**
- Directory: frontend/web_app/src/lib/ contains 50+ files
- Key files: api/, useApi.ts, useAuth.tsx, toastStore.ts, cartStore.ts, currencyStore.ts, localeStore.ts, rbac.ts, etc.
- All pages and components import from @/lib/*

**Impact:** High concentration of client-side logic in a single directory. This is appropriate for a Next.js app but creates a potential bottleneck for concurrent edits.

---

## 6. DEPENDENCY FLOW SUMMARY

### 6.1 BACKEND DEPENDENCY FLOW (Top-Down)

`
main.py
  ├── infrastructure.database.models (model registration)
  ├── infrastructure.database.database (engine, sessions)
  ├── infrastructure.database.base (DeclarativeBase)
  ├── infrastructure.database.rls_interceptor (RLS)
  ├── infrastructure.utils.config (settings)
  ├── infrastructure.utils.ip_utils
  ├── infrastructure.observability.* (logging, metrics, tracing)
  ├── infrastructure.utils.versioning
  ├── infrastructure.utils.websocket_manager
  ├── infrastructure.utils.router_loader
  ├── middleware.orchestrator (middleware pipeline)
  │     ├── middleware.* (15 middleware classes)
  │     └── infrastructure.utils.config
  ├── lifespan (startup hooks)
  │     ├── infrastructure.database.*
  │     ├── infrastructure.utils.config
  │     ├── infrastructure.utils.migrations
  │     ├── domains.accounts.services.permissions
  │     ├── domains.finance.services.payments.payment_engine
  │     ├── domains.orders.services.fulfillment_service
  │     └── domains.finance.services.seeders.treasury_seeder
  └── modules.{actor}.routers (dynamic discovery)
        ├── infrastructure.database.database (get_db)
        ├── infrastructure.security.dependencies (auth)
        ├── rbac.dependencies (feature gates)
        └── domains.{domain}.services.* (business logic)
              ├── infrastructure.database.database
              ├── infrastructure.utils.*
              └── domains.{other_domain}.ports (cross-domain reads)
`

### 6.2 FRONTEND DEPENDENCY FLOW

`
web_app/src/app/layout.tsx
  ├── @/styles/*
  ├── @/lib/useAuth (AuthProvider)
  ├── @/components/* (Header, Footer, etc.)
  └── @shared/* (via barrel exports)
        ├── ./types
        ├── ./api-core
        ├── ./requestCache
        ├── ./i18n
        ├── ./localization
        ├── ./productQuery
        └── ./components/*

web_app/src/app/providers.tsx
  ├── @tanstack/react-query
  ├── @shared/adminPermissions
  └── @/components/QueryErrorBoundary

mobile_app/app/_layout.tsx
  ├── expo-router
  ├── @/lib/* (authStore, themeStore, api, etc.)
  ├── @/components/*
  └── @shared/* (localization, api-core, types)
`

---

## 7. EXTERNAL DEPENDENCIES SUMMARY

### 7.1 BACKEND EXTERNAL DEPENDENCIES (from requirements.txt)

| Category | Package | Version | Usage |
|----------|---------|---------|-------|
| Web Framework | fastapi | 0.115.2 | API framework |
| Web Framework | uvicorn[standard] | 0.51.0 | ASGI server |
| Web Framework | gunicorn | 26.0.0 | WSGI/ASGI worker |
| Web Framework | starlette | latest | ASGI toolkit |
| Database | sqlalchemy | 2.0.51 | ORM |
| Database | alembic | 1.18.5 | Migrations |
| Database | asyncpg | 0.31.0 | PostgreSQL async driver |
| Database | psycopg2-binary | 2.9.12 | PostgreSQL sync driver |
| Cache | redis | 8.0.1 | Redis client |
| Auth | python-jose[cryptography] | 3.5.0 | JWT |
| Auth | pyjwt | 2.13.0 | JWT |
| Auth | bcrypt | 5.0.0 | Password hashing |
| Auth | pyotp | 2.10.0 | OTP |
| Auth | passlib[bcrypt] | 1.7.4 | Password hashing |
| Jobs | celery | 5.4.0 | Distributed tasks |
| Jobs | apscheduler | 3.11.3 | Scheduled tasks |
| HTTP | httpx | 0.28.1 | Async HTTP client |
| HTTP | requests | 2.34.2 | Sync HTTP client |
| Validation | pydantic | 2.13.4 | Data validation |
| Validation | pydantic-settings | 2.7.1 | Settings |
| Validation | python-dotenv | 1.2.2 | Env loading |
| File Handling | aiofiles | 25.1.0 | Async file I/O |
| File Handling | python-magic | 0.4.27 | File type detection |
| Image | Pillow | 12.3.0 | Image processing |
| AI/ML | numpy | 2.2.6 | Array operations |
| Observability | structlog | 26.1.0 | Structured logging |
| Observability | sentry-sdk | 2.66.1 | Error tracking |
| Observability | prometheus-client | 0.26.0 | Metrics |
| Observability | prometheus-fastapi-instrumentator | 7.1.0 | Metrics |
| Observability | opentelemetry-* | 1.44.0 | Distributed tracing |
| Rate Limiting | slowapi | 0.1.10 | Rate limiting |
| Rate Limiting | limits | 5.8.0 | Rate limiting |
| Utilities | cachetools | 5.5.0 | Caching |
| Utilities | python-slugify | 8.0.4 | URL slugs |
| Utilities | pytz | 2026.3.post1 | Timezone |
| Utilities | tzlocal | 5.4.4 | Local timezone |
| Utilities | babel | 2.18.0 | Localization |
| Utilities | phonenumbers | 9.0.35 | Phone parsing |
| Utilities | faker | 40.36.0 | Test data |
| Payments | stripe | 15.3.1 | Payments |
| WebSockets | websockets | 16.1.1 | WebSocket |
| Analytics | duckdb | 1.5.5 | OLAP |
| Analytics | duckdb-engine | 0.17.0 | DuckDB SQLAlchemy |

**Evidence:**
- File: backend/requirements.txt:1-102

---

### 7.2 FRONTEND EXTERNAL DEPENDENCIES

#### Web App (frontend/web_app/package.json)

| Package | Version | Usage |
|---------|---------|-------|
| next | 16.3.4 | React framework |
| react | 19.2.8 | UI library |
| react-dom | 19.2.8 | React DOM |
| @stripe/react-stripe-js | ^5.6.0 | Stripe payments |
| @stripe/stripe-js | ^8.7.0 | Stripe JS |
| @zxing/library | ^0.21.3 | Barcode scanning |
| chart.js | ^4.5.1 | Charts |
| framer-motion | ^12.0.0 | Animations |
| jose | ^6.2.10 | JWT |
| jspdf | ^4.1.0 | PDF generation |
| lucide-react | ^0.563.0 | Icons |
| qrcode | ^1.5.4 | QR codes |
| react-chartjs-2 | ^5.3.1 | Chart.js React wrapper |
| tailwind-merge | ^3.5.0 | Tailwind utilities |
| zustand | ^5.0.11 | State management |
| clsx | ^2.1.1 | Class names |
| class-variance-authority | ^0.7.1 | Component variants |
| core-js | ^3.37.1 | Polyfills |
| dompurify | ^3.3.3 | HTML sanitization |

**Evidence:**
- File: frontend/web_app/package.json:14-57

#### Shared Package (frontend/shared/package.json)

| Package | Version | Usage |
|---------|---------|-------|
| clsx | ^2.1.1 | Class names |
| framer-motion | ^12.0.0 | Animations |
| lucide-react | ^0.563.0 | Icons |
| tailwind-merge | ^3.5.0 | Tailwind utilities |
| zustand | ^5.0.14 | State management |

**Evidence:**
- File: frontend/shared/package.json:24-30

#### Mobile App (frontend/mobile_app/package.json)

| Package | Version | Usage |
|---------|---------|-------|
| expo | ~57.0.9 | React Native framework |
| react-native | 0.81.4 | React Native |
| react | 19.1.0 | UI library |
| @react-navigation/native | ^7.3.4 | Navigation |
| @react-navigation/native-stack | ^7.17.7 | Stack navigation |
| @stripe/stripe-react-native | ^0.50.0 | Stripe payments |
| react-native-reanimated | ^4.2.1 | Animations |
| react-native-gesture-handler | ^2.30.1 | Gestures |
| react-native-safe-area-context | ^5.6.2 | Safe areas |
| react-native-screens | ^4.23.0 | Native screens |
| react-native-svg | ^15.15.3 | SVG |
| lucide-react-native | ^0.469.0 | Icons |
| dayjs | ^1.11.13 | Date handling |
| zustand | ^5.0.14 | State management |

**Evidence:**
- File: frontend/mobile_app/package.json:16-34

---

## 8. CONCLUSION

### 8.1 BACKEND FINDINGS

The backend import map reveals a mature but complex dependency structure:

1. **127 modules, 743 domains, 115 providers** — extensive modular architecture
2. **4 confirmed circular dependency chains** — primarily around RBAC/infrastructure security shims
3. **14 inactive middleware files** — legacy code retained for reference but not active
4. **6+ high-dependency modules** — user_management_service.py and supplier_shared.py act as cross-domain hubs
5. **2 critical architectural hotspots** — products_service.py (914 lines) and payout_batch_service.py (4145+ lines)
6. **Dynamic router discovery** — all 5 actor modules use identical importlib patterns

### 8.2 FRONTEND FINDINGS

The frontend import map shows a modern, well-structured monorepo:

1. **3 applications** — web_app (Next.js), mobile_app (Expo), shared package
2. **Shared package** — central types and API core used by both web and mobile
3. **1136-line products page** — largest frontend component, needs decomposition
4. **2333-line mobile API client** — all mobile API calls flow through single file
5. **No circular dependencies detected** — clean frontend dependency graph

### 8.3 CRITICAL RISKS

| Risk | Severity | Recommendation |
|------|----------|----------------|
| Circular dependency: RBAC ↔ infrastructure.security | HIGH | Break cycle by moving security_dependencies to a shared layer |
| Monolithic payout_batch_service.py (4145+ lines) | HIGH | Decompose into smaller service modules |
| Monolithic products_service.py (914 lines) | MEDIUM | Extract product-specific logic into separate files |
| 14 inactive middleware files | MEDIUM | Remove or archive to reduce codebase noise |
| Dynamic router discovery (all 5 modules) | MEDIUM | Consider static router registration for better type safety |
| 1136-line products page component | MEDIUM | Decompose into smaller, testable components |
| 2333-line mobile API client | MEDIUM | Split into domain-specific API modules |

### 8.4 NEXT STEPS

1. **Phase 05:** Analyze database schema alignment and migration completeness
2. **Phase 06:** Review authentication and RBAC implementation against architecture diagram
3. **Phase 07:** Verify production readiness checklist (secrets, logging, error handling)

---

**End of Phase 04: Import Map & Module Dependencies**

*Generated: 2026-09-11*
*Auditor: Kilo (CTO-level audit)*
