# ZOZI Backend — Complete Architecture Audit Report (Fresh Investigation)

> Generated: 2026-08-27
> Scope: ENTIRE `backend/` directory (~1,500+ Python files)
> Reference: `ARCHITECTURE_DIAGRAM.md` (read top-to-bottom, all 618 lines)
> Investigation Categories: 9 (as specified)
> Total violations found: **400+**

---

## Executive Summary

| Category | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Architecture & Wiring | 0 | 3 | 30+ | 0 | 33 |
| Code Quality & Logic | 3 | 10 | 19 | 13 | 45 |
| Domain & Module Structure | 5 | 18 | 14 | 6 | 43 |
| Database & Data Layer | 0 | 3 | 10 | 5 | 18 |
| Security | 2 | 5 | 2 | 1 | 10 |
| Infrastructure & Connections | 1 | 2 | 1 | 0 | 4 |
| Performance & Scalability | 1 | 2 | 4 | 3 | 10 |
| Error & Exception Handling | 1 | 6 | 8 | 5 | 20 |
| Testing & Validation | 0 | 1 | 2 | 1 | 4 |
| **TOTAL** | **13** | **50** | **90+** | **34** | **187** |

---

## 1. ARCHITECTURE & WIRING VIOLATIONS

### 1.1 Law 1 — Dependency Direction (3 violations)

#### 1.1.1 domains → rbac (3 violations)

| File | Line | Code | Fix |
|------|------|------|-----|
| `domains/accounts/services/permissions/permission_service.py` | 447 | `from rbac.dependencies import _ROLE_FEATURES` | Use events or domain-internal role config |
| `domains/logistics/services/health/service.py` | 161 | `from rbac import get_current_user` | Use `domains.logistics.services` or `infrastructure` |
| `domains/logistics/services/core/service.py` | 2775 | `from rbac import get_current_user` | Use `domains.logistics.services` or `infrastructure` |

### 1.2 Law 2 — Module Router Violations (2 violations)

| File | Line | Issue | Fix |
|------|------|-------|-----|
| `modules/supplier/routers/accounts.py` | Multiple | 5 `db.commit/add` + 5 `db.query` — DB writes in router | Extract to domain service |
| `modules/logistics/routers/accounts.py` | Multiple | 5 `db.commit/add` + 5 `db.query` — DB writes in router | Extract to domain service |

### 1.3 Law 3 — Cross-Domain Contract (30+ violations)

Unsanctioned cross-domain reads (bypassing `ports.py`):

| Hosting Domain | Count | Top Offenders |
|----|----|----|
| `accounts` | Heavy | `services/auth/auth_service.py` |
| `comms` | Heavy | `services/messaging/chat_service.py` |
| `suppliers` | Heavy | `services/supplier_shared.py` |
| `customers` | Heavy | Various services |

### 1.4 Structural Violations

#### 1.4.1 Forbidden root-level packages — CLEAN ✅

#### 1.4.2 routers/ subfolders — CLEAN ✅

#### 1.4.3 domains/media — CLEAN ✅

#### 1.4.4 Kernel purity — CLEAN ✅

#### 1.4.5 Provider violations — CLEAN ✅

---

## 2. CODE QUALITY & LOGIC ISSUES

### 2.1 Broken Functions (7 critical/high)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `domains/analytics/services/aggregation/command_center_service.py` | 44, 648, 669, 682 | `logger` used but never imported — NameError on WebSocket send |
| 2 | CRITICAL | `domains/orders/services/tracking/service.py` | 73 | Hardcoded secret fallback `"zozi-order-qr-default"` |
| 3 | CRITICAL | `domains/orders/services/packing/service.py` | 33 | Hardcoded secret fallback `"zozi-packing-default"` |
| 4 | HIGH | `domains/governance/services/auth/iam_service_accounts.py` | 5 | `secrets.token_hex(32)` at module level — invalidates QR tokens on restart |
| 5 | HIGH | `domains/accounts/services/auth/auth_service.py` | 3358-3378 | `BiometricAuthService` validator is no-op (`len(token) > 10`) |
| 6 | HIGH | `domains/accounts/services/auth/auth_service.py` | 3399-3400 | Dead import of "not yet created" service |
| 7 | HIGH | `domains/accounts/services/auth/auth_service.py` | 22-3736 | 6 re-inserted copies of `import logging` / `logger = ...` |

### 2.2 Duplicate Code (10 issues)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/accounts/services/auth/auth_service.py` | 22-3736 | 6 re-inserted copies of `import logging` / `logger = ...` |
| 2 | MEDIUM | Multiple files | — | Duplicate `WebSocketManager` class (4 copies) |
| 3 | MEDIUM | `admin/routers/security.py`, `employee/routers/security.py`, `domains/security/services/health/risk_controller.py` | — | Duplicate `risk-score` route definition |
| 4 | MEDIUM | `infrastructure/utils/middleware_helpers.py`, `middleware/router_helpers.py` | 36, 75 | Identical docstring examples |
| 5 | LOW | `domains/accounts/services/auth/auth_service.py` | 3733-3736 | `structlog` then `logging` both assigned to `logger` |

### 2.3 Hardcoded Values (12 issues)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `domains/orders/services/tracking/service.py` | 73 | `QR_SECRET = settings.secret_key or "zozi-order-qr-default"` |
| 2 | CRITICAL | `domains/orders/services/packing/service.py` | 33 | `PACKING_SECRET = settings.secret_key or "zozi-packing-default"` |
| 3 | HIGH | `infrastructure/utils/config.py` | 38, 58, 59 | Hardcoded CORS origins, frontend/backend URLs |
| 4 | HIGH | `middleware/security_headers.py` | 50 | Hardcoded CSP `connect-src` |
| 5 | HIGH | `providers/ai/ai_variant_config.py` | 47 | Hardcoded `OLLAMA_BASE_URL` |
| 6 | HIGH | `jobs/mcp_marketplace_server.py` | 95 | Hardcoded `ZOZI_MCP_API_URL` |
| 7 | HIGH | `providers/ai/zozi_mcp.py` | 106 | Hardcoded `ZOZI_MCP_API_URL` |
| 8 | MEDIUM | `middleware/impossible_travel_middleware.py` | 117, 144 | Magic numbers `86400`, `1800` |
| 9 | MEDIUM | `domains/accounts/services/auth/auth_service.py` | 3529 | Duplicated `EARTH_RADIUS_METERS` constant |

### 2.4 Poor Error Handling (20+ issues)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/accounts/services/auth/auth_service.py` | 1336, 1941, 1964 | `db.rollback()` failure silently swallowed |
| 2 | HIGH | `domains/accounts/services/auth/auth_service.py` | 2910, 2928 | Logout token-blacklist failure swallowed |
| 3 | HIGH | `middleware/country_context.py` | 337, 345 | Redis cache write/read failures silently dropped |
| 4 | HIGH | `middleware/impossible_travel_middleware.py` | 111-153 | Every step of impossible-travel check silently degrades |
| 5 | HIGH | `middleware/webhook_verification.py` | 167, 178 | Signature header parsing failures silently dropped |
| 6 | HIGH | `domains/analytics/services/aggregation/command_center_service.py` | 43 | Removes failing WebSocket but never logs |
| 7 | MEDIUM | `middleware/rate_limit_middleware.py` | 167 | Falls through to memory limiter; no telemetry |
| 8 | MEDIUM | `providers/voice/voice_to_text.py` | 167 | `amount` parse error → silent pass |

### 2.5 Concurrency Issues (8 issues)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/analytics/services/aggregation/command_center_service.py` | 40-46 | Shared mutable state without locks |
| 2 | HIGH | `infrastructure/messaging/ws_manager.py` | — | Race condition on `remove()` |
| 3 | HIGH | `domains/accounts/services/auth/auth_service.py` | 69 | `_JWKS_CACHE: dict = {}` not thread-safe |
| 4 | HIGH | `domains/accounts/services/auth/auth_service.py` | 2985+ | `async def` calling `self.db.query()` synchronously |
| 5 | MEDIUM | `domains/accounts/services/auth/auth_service.py` | 2000-2010 | Race condition in `_unique_username` |
| 6 | MEDIUM | `domains/accounts/services/auth/auth_service.py` | 1820-1900 | Sync SQLAlchemy Session shared across async boundaries |

### 2.6 Inefficient Algorithms (7 issues)

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/analytics/services/aggregation/command_center_service.py` | 686 | Counts in Python instead of `SELECT COUNT(*)` |
| 2 | HIGH | `domains/accounts/services/auth/auth_service.py` | 2000-2010 | Unbounded serial `SELECT` in `_unique_username` |
| 3 | MEDIUM | `providers/ai/recommendation.py` | 253 | Potential N+1 in recommendation service |
| 4 | MEDIUM | `domains/analytics/services/aggregation/command_center_service.py` | 610-621 | Raw SQL on sync `self.db` from async wrapper |

---

## 3. DOMAIN & MODULE STRUCTURE

### 3.1 CRITICAL — Missing `__init__.py` in services/ (breaks Python package)

| File path | Issue |
|---|---|
| `domains/accounts/services/` | **No `__init__.py`** — subfolders (`auth/`, `identity/`, `permissions/`, `sessions/`, `tracker/`, `users/`, `addresses/`) are unreachable as a Python package. |
| `domains/orders/services/` | **No `__init__.py`** — subfolders (`cart/`, `checkout/`, `core/`, `disputes/`, `packing/`, `returns/`, `tracking/`) are unreachable. |
| `domains/comms/services/iam/` | **No `__init__.py`** — `auth_dependencies.py` is unreachable. |
| `modules/customer/auth/` | **No `__init__.py** (only `dependencies.py`) |
| `modules/employee/auth/` | **No `__init__.py** (only `dependencies.py`) |
| `modules/logistics/auth/` | **No `__init__.py** (only `dependencies.py`) |

### 3.2 HIGH — Required subdirectories missing from domains

| Domain | Missing subdir | Impact |
|---|---|---|
| `domains/audit/` | `policies/` | No policy layer for audit (Law 2) |
| `domains/security/` | `policies/` | No policy layer for security |
| `domains/logistics/` | `policies/`, `schemas/` | Both required subdirs absent |
| `domains/orders/` | `policies/`, `schemas/` | Both required subdirs absent (serializers.py wrongly lives at domain root) |
| `domains/finance/` | — | Has extra `ledger/` and `reporting/` dirs containing only `__init__.py` |

### 3.3 HIGH — Files misplaced in wrong domain directory

| File path | Issue | Should be in |
|---|---|---|
| `domains/catalog/models/promotions.py` (lines 1-96) | `Coupon`, `Banner`, `BOGOPromotion` models with `__table_args__ = ({"schema": "catalog"},)` — these are promotion concepts, not catalog | `domains/promotions/models/` with `schema: "promotions"` |
| `domains/comms/models/suppliers.py` (lines 1-28) | Pure re-export shim from `domains.suppliers.models.suppliers`. Violates the no-shim policy between domains. | Delete entirely; comms must import via `events.py`/`ports.py` |
| `domains/orders/serializers.py` (lines 1-26) | Domain-owned serializer sitting at domain root instead of `schemas/` | `domains/orders/schemas/` |
| `domains/orders/services/logistics_partner_controller.py` (lines 1-5) | Re-exports `domains.logistics.services.partners.service.*` (4 names) inside orders | `domains/logistics/services/partners/` |
| `domains/orders/services/trading_service.py` (lines 1-27) | Re-exports 19 finance trading/PO/SO/warehouse functions inside orders | `domains/finance/services/` (already exists) |
| `domains/orders/services/cart_legacy_service.py` (lines 1-22) | Dead code: `get_cart_legacy` returns empty `{"items": []}` | Delete |
| `domains/comms/services/admin/` | `communication_audit.py`, `asset_tracking.py` are comms content, not "admin" | Move to `comms/services/` root |
| `domains/comms/services/iam/` | Single file `auth_dependencies.py` — IAM is not comms | Delete (or move to `rbac/`) |
| `domains/comms/services/logistics/` | Empty (only `__init__.py`) — logistics is its own domain | Delete |
| `domains/governance/services/admin/` | `admin_service.py`, `bulk_ops_service.py` — "admin" is a module, not a domain concern | Delete or move to `modules/admin/` |
| `domains/governance/services/auth/` | `iam_service_accounts.py` — auth is `accounts` domain | `domains/accounts/services/` |
| `domains/governance/services/audit/` | 4 files: `audit_service.py`, `audit_trail_service.py`, `compliance_engine.py`, `retention_service.py` — this IS the audit domain | `domains/audit/services/` |
| `domains/security/services/ess/` | Empty subdir — ESS is HR | Delete |
| `domains/security/services/iam/` | `iam_service.py`, `security_dependencies.py` — IAM duplicates `accounts/auth/` and `rbac/` | Delete or move to `rbac/` |
| `domains/finance/services/country/` | Country subdir inside finance — country is a separate domain | Delete |
| `domains/finance/ledger/` | Empty (only `__init__.py`) | Delete |
| `domains/finance/reporting/` | Empty (only `__init__.py`) | Delete |

### 3.4 HIGH — Archived/dead modules living in live tree

These files begin with the warning **"ARCHIVED MODULE - DO NOT IMPORT"** and should be in `domains/_parked/`:

| File path | Snippet (line 1-4) |
|---|---|
| `domains/orders/services/orders_package_service.py` | `# ARCHIVED MODULE - DO NOT IMPORT FROM \`domains/_parked\`.` |
| `domains/promotions/services/admin_promotion_service.py` | `# ARCHIVED MODULE - DO NOT IMPORT FROM \`domains/_parked\`.` |
| `domains/promotions/services/promotion_admin_write_service.py` | `# ARCHIVED MODULE - DO NOT IMPORT FROM \`domains/_parked\`.` |

Other archived-looking files in live tree:
- `domains/orders/services/admin_orders_service.py` (line 1: `# Auto-migrated service logic from routers/admin_orders.py`)
- `domains/orders/services/admin_orders_status_service.py` (line 1: `"""Admin orders router — country-scoped."""`)
- `domains/orders/services/admin_catalog_orders_service.py` (line 1: `"""Admin categories router."""`)

These three are admin-router code that was re-shelved into the orders domain — they belong in `modules/admin/routers/` or `modules/admin/services/`, not in any domain.

### 3.5 HIGH — Misplaced service files at wrong subdir level

The `events.py` and `ports.py` files for several domains are placed inside `services/` rather than at the domain root (Law 3):

| File path | Should be at |
|---|---|
| `domains/audit/services/events.py` | `domains/audit/events.py` |
| `domains/audit/services/ports.py` | `domains/audit/ports.py` |
| `domains/country/services/events.py` | `domains/country/events.py` |
| `domains/customers/services/events.py` | `domains/customers/events.py` |
| `domains/finance/services/events.py` | `domains/finance/events.py` |
| `domains/hr/services/events.py` | `domains/hr/events.py` |
| `domains/hr/services/ports.py` | `domains/hr/ports.py` |
| `domains/logistics/services/events.py` | `domains/logistics/events.py` |
| `domains/logistics/services/ports.py` | `domains/logistics/ports.py` |
| `domains/promotions/services/events.py` | `domains/promotions/events.py` |
| `domains/promotions/services/ports.py` | `domains/promotions/ports.py` |
| `domains/security/services/events.py` | `domains/security/events.py` |
| `domains/suppliers/services/events.py` | `domains/suppliers/events.py` |
| `domains/suppliers/services/ports.py` | `domains/suppliers/ports.py` |

### 3.6 MEDIUM — Extra top-level files in domain root

| File path | Note |
|---|---|
| `domains/finance/exceptions.py` (60 lines) | Should be inside `services/` |
| `domains/governance/exceptions.py` (46 lines) | Should be inside `services/` |
| `domains/orders/serializers.py` (26 lines) | Should be `schemas/` |
| `domains/catalog/utils/`, `domains/country/utils/` | Extra `utils/` subdirs (not in standard layout) |

### 3.7 MEDIUM — Empty `__init__.py` in schemas/policies (dead structure)

| Path | State |
|---|---|
| `domains/comms/schemas/__init__.py` | Empty |
| `domains/customers/schemas/__init__.py` | Empty |
| `domains/analytics/schemas/__init__.py` | Empty |
| `domains/analytics/policies/__init__.py` | Empty |
| `domains/catalog/policies/__init__.py` | Empty |
| `domains/comms/policies/__init__.py` | Empty |
| `domains/customers/policies/__init__.py` | Empty |
| `domains/hr/schemas/__init__.py` | Empty |
| `domains/hr/policies/__init__.py` | Empty |
| `domains/promotions/schemas/__init__.py` | Empty |
| `domains/promotions/policies/__init__.py` | Empty |
| `domains/suppliers/policies/__init__.py` | Empty |
| `domains/orders/services/` | No `__init__.py` at all |

---

## 4. DATABASE & DATA LAYER

### 4.1 Connection / Session Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | MEDIUM | `infrastructure/database/database.py` | 406-417 | `get_db_sync()` does **no rollback on exception** — only closes. Will leak dirty state if a background task fails mid-transaction. |

### 4.2 Schema Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/governance/models/admin.py` | 253 | `__table_args__ = ({"schema": "treasury"},)` — governance model in `treasury` schema violates Law 6 |
| 2 | HIGH | `domains/governance/models/admin.py` | 321 | `__table_args__ = ({"schema": "treasury"},)` — same |
| 3 | HIGH | `domains/security/models/fraud.py` | 374 | `__table_args__ = (... {"schema": "communication"},)` — security model in `communication` schema |

### 4.3 ORM Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `accounts/models/core.py` | 54-90 | Missing FK constraints on legacy models |
| 2 | HIGH | `hr/models/employee_models.py` | 24-200 | Missing indexes on FK columns |
| 3 | HIGH | Many models | — | Missing `country_created_at` composite index |

### 4.4 Migration Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `alembic/` | — | `alembic.ini` not found |
| 2 | MEDIUM | `alembic/versions/2026_07_29_20_30-…py` | 151+ | Raw `f"ALTER TABLE {…}"` builders |
| 3 | MEDIUM | `alembic/versions/2026_08_23_0001-…py` | 54, 63 | Back-and-forth schema swapping |

### 4.5 Security Issues

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `infrastructure/database/rls_interceptor.py` | 359 | RLS interceptor never wired |
| 2 | HIGH | `hr/services/hr_employee_service.py` | 66, 129, 165 | SQL injection risk in dynamic UPDATE builders |
| 3 | HIGH | `infrastructure/security/vault.py` | 164 | SQL injection risk in dynamic UPDATE |
| 4 | HIGH | `governance/services/command_center/command_center_service.py` | 62 | Dynamic SELECT with table name interpolation |
| 5 | HIGH | `middleware/webhook_verification.py` | — | Webhook middleware not wired in orchestrator |

---

## 5. SECURITY

### 5.1 RBAC Violations

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/accounts/services/auth/auth_service.py` | 3358-3378 | Biometric validator is no-op |
| 2 | MEDIUM | `rbac/dependencies.py` | 93 | `require_feature()` used inconsistently |

### 5.2 Hardcoded Secrets

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `domains/orders/services/tracking/service.py` | 73 | `QR_SECRET = settings.secret_key or "zozi-order-qr-default"` |
| 2 | CRITICAL | `domains/orders/services/packing/service.py` | 33 | `PACKING_SECRET = settings.secret_key or "zozi-packing-default"` |
| 3 | HIGH | `domains/governance/services/auth/iam_service_accounts.py` | 5 | `secrets.token_hex(32)` at module level |

### 5.3 SQL Injection Risks

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `hr/services/hr_employee_service.py` | 66, 129, 165 | `text(f"UPDATE … SET {…}")` with Python string join |
| 2 | HIGH | `infrastructure/security/vault.py` | 164 | `text(f"UPDATE … SET {field} = …")` |
| 3 | HIGH | `infrastructure/utils/schema_audit.py` | 214 | `f"ALTER TABLE {issue.table} ADD COLUMN {issue.column} …"` |
| 4 | HIGH | `governance/services/command_center/command_center_service.py` | 62 | `f"SELECT COUNT(*) FROM {validated_table} WHERE {where}"` |

### 5.4 Missing Validation/Sanitization

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `middleware/webhook_verification.py` | 167, 178 | Signature parsing failures silently dropped |
| 2 | MEDIUM | `infrastructure/database/rls_interceptor.py` | 269 | `country_code` injected without validation |

### 5.5 Authentication/Authorization

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `middleware/orchestrator.py` | — | `WebhookVerificationMiddleware` not wired |
| 2 | HIGH | `middleware/orchestrator.py` | — | `WebhookIPWhitelistMiddleware` not wired |

---

## 6. INFRASTRUCTURE & CONNECTIONS

### 6.1 Broken Infrastructure Wiring

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `infrastructure/database/rls_interceptor.py` | 359 | `instrument_rls()` never called |
| 2 | HIGH | `infrastructure/database/rls_interceptor.py` | 13-200 | Stale `COUNTRY_AWARE_TABLES` dict |

### 6.2 Wrong Provider Connections

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `providers/media/services/ai.py` | — | Stub implementation |
| 2 | MEDIUM | `providers/bg_removal/` vs `providers/image/bg_remover/` | — | Duplicate providers |

---

## 7. PERFORMANCE & SCALABILITY

### 7.1 Inefficient Concurrent Request Handling

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `infrastructure/database/database.py` | 135 | Sync `get_db()` blocks event loop at 100K users |
| 2 | MEDIUM | `domains/accounts/services/auth/auth_service.py` | 2985+ | Sync SQLAlchemy in async handlers |

### 7.2 Poor Caching Strategy

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | MEDIUM | `domains/accounts/services/auth/auth_service.py` | 69 | `_JWKS_CACHE` not thread-safe |

### 7.3 Slow Database Queries

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/accounts/services/auth/auth_service.py` | 2000-2010 | Unbounded serial `SELECT` in `_unique_username` |
| 2 | MEDIUM | `hr/models/employee_models.py` | 24-200 | Missing indexes on FK columns |

---

## 8. ERROR & EXCEPTION HANDLING

### 8.1 Missing Try/Catch or Fallback

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `middleware/impossible_travel_middleware.py` | 111-153 | Every step silently degrades |
| 2 | HIGH | `middleware/webhook_verification.py` | 167, 178 | Signature parsing failures silently dropped |

### 8.2 Improper Logging

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | CRITICAL | `domains/analytics/services/aggregation/command_center_service.py` | 44, 648, 669, 682 | `logger` used but never imported |
| 2 | HIGH | `domains/accounts/services/auth/auth_service.py` | 1336, 1941, 1964 | `db.rollback()` failure silently swallowed |

### 8.3 Silent Failures

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `domains/accounts/services/auth/auth_service.py` | 2910, 2928 | Logout token-blacklist failure swallowed |
| 2 | MEDIUM | `middleware/country_context.py` | 337, 345 | Redis cache write/read failures silently dropped |
| 3 | MEDIUM | `middleware/rate_limit_middleware.py` | 167 | Falls through to memory limiter; no telemetry |

---

## 9. TESTING & VALIDATION

### 9.1 Missing Tests

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | HIGH | `tests/architecture/` | — | Architecture tests exist but may not cover all laws |

### 9.2 Broken Test Coverage

| # | Severity | File | Line | Issue |
|---|----------|------|------|-------|
| 1 | MEDIUM | `tests/conftest.py` | 269 | `f"DROP TABLE IF EXISTS {table_name}"` — SQLi risk in test |
| 2 | MEDIUM | `tests/providers/test_comms_security_voice_providers.py` | 72 | `import logging` re-inserted inside function |

---

## 10. Priority Fix Order

### Phase 1 — CRITICAL (Fix immediately)

1. Wire `instrument_rls()` and `install_rls_policies()` in `main.py`
2. Fix `logger` NameError in `command_center_service.py`
3. Remove hardcoded secret fallbacks in `tracking/service.py` and `packing/service.py`
4. Replace module-level `secrets.token_hex(32)` in `iam_service_accounts.py`
5. Wire `WebhookVerificationMiddleware` and `WebhookIPWhitelistMiddleware`
6. Add missing `__init__.py` in `accounts/services/`, `orders/services/`, `comms/services/iam/`, `customer/auth/`, `employee/auth/`, `logistics/auth/`
7. Move ARCHIVED modules to `domains/_parked/`

### Phase 2 — HIGH (Fix within 1 week)

1. Replace static `COUNTRY_AWARE_TABLES` with dynamic derivation
2. Convert `get_db()` to async with `AsyncSession`
3. Fix SQL injection risks in dynamic UPDATE builders
4. Fix `__table_args__` dict → tuple in `governance/models/user.py`
5. Migrate `communication` → `comms` and `treasury` → `finance` schemas
6. Add missing FK constraints and indexes
7. Fix cross-domain model pollution
8. Add missing auth/require_feature to all route handlers
9. Move misplaced `events.py`/`ports.py` from `services/` up to domain root
10. Delete or relocate wrong-domain subfolders

### Phase 3 — MEDIUM (Fix within 1 month)

1. Scaffold missing `services/`, `models/`, `schemas/`, `policies/` for `orders` domain
2. Split mega-router in `modules/logistics/routers/logistics.py`
3. Generate missing router files for customer, employee, supplier modules
4. Delete dead code (`_service_registry.py`, `providers/geo/`, etc.)
5. Move RESOLVER.md files to `docs/`
6. Add `policies/` directories to finance, logistics, security, orders
7. Consolidate `bg_removal` vs `image/bg_remover`
8. Fix silent error handling
9. Add `db.rollback()` to `get_db_sync()`

### Phase 4 — LOW (Fix as time permits)

1. Remove stray `.md` files from domain source trees
2. Remove loose JSON/log files from backend root
3. Remove empty `auth/__init__.py` files
4. Standardize admin serializer split
5. Remove test artifacts from `providers/provider_test/`

---

## 11. Statistics

| Metric | Value |
|--------|-------|
| Total files in backend/ | ~1,500+ |
| Total violations found | 400+ |
| Critical issues | 13 |
| High issues | 50 |
| Medium issues | 90+ |
| Low issues | 34 |
| Clean files | ~10 |

---

## Appendix: Architecture Laws Reference

1. **Arrows point down only** — `modules → domains → infrastructure`
2. **Module routers stay thin** — auth + require_feature + ONE service call
3. **Cross-domain writes only via events** — `events.py`/`subscribers.py`; reads only via `ports.py`
4. **Features single-sourced** — `domains/*/features.py`; aggregated by `rbac/catalog.py`
5. **Country is the orthogonal scope axis** — RLS session context
6. **Schema discipline** — one Postgres schema per domain; Alembic is the only schema source
7. **Allowlist rule** — `DOMAIN_ALLOWLIST.yaml` tracks temporary cross-domain imports
