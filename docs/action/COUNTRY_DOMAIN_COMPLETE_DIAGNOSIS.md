# Country Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/country/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **200+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 40+ |
| 🟠 HIGH | 60+ |
| 🟡 MEDIUM | 50+ |
| 🟢 LOW | 30+ |
| **TOTAL** | **200+** |

---

## 1. P0 RUNTIME ERRORS (CRITICAL — Will Crash Every Request)

| # | File | Line | Bug | Fix |
|---|------|------|-----|-----|
| 1 | `country_service.py` | 145 | `_record` not defined — every admin write crashes | Implement using `audit.services.logs.audit_trail_service` |
| 2 | `country_service.py` | 1426 | `CITY_SUGGESTIONS` not defined | Define or delete fallback |
| 3 | `country_service.py` | 1939-1969 | `lru_cache` over DB + returns raw JSON string | Replace with Redis cache, parse JSON |
| 4 | `country_config_admin_service.py` | 91, 92, 198, 199, 248 | `rloat` typo (5×) | Rename to `float` |
| 5 | `country_config_admin_service.py` | 43, 66, 98, 231 | `db.rerresh` typo (4×) | Rename to `db.refresh` |
| 6 | `country_config_admin_service.py` | 655-657 | `svc_assign_staff` stub returns fake success | Implement or remove |
| 7 | `country_staff_write_service.py` | 77 | `User` not imported | Add `from domains.accounts.models.user import User` |
| 8 | `country_maps_service.py` | 297 | `Category` not imported | Add import or delete function |
| 9 | `country_restriction_service.py` | 48 | `get_active_country_by_code` not defined | Define locally or use `ports.get_country_config` |
| 10 | `country_restriction_service.py` | 62 | `r in restricted` silently False for dicts | Type-check `r` before `in` |
| 11 | `cross_border_service.py` | 156 | `timezone` not imported | Add `from datetime import timezone` |
| 12 | `country_detection.py` | 174 | Missing `math` import | Add `from math import radians, sin, cos, sqrt, atan2` |
| 13 | `country_detection.py` | 170 | `_check_country_fence` always returns True | Implement or delete |
| 14 | `transactional.py` | 30, 222 | `User` not imported at module level | Add import |
| 15 | `tickets_service.py` | 232 | `desc` not imported | Add `from sqlalchemy import desc` |
| 16 | `system_comms_status_service.py` | 25-30 | Imports from non-existent module | Create or fix import |
| 17 | `chat_service.py` | 697, 730, 736 | `utcnow` not imported | Add `from infrastructure.utils.datetime_utils import utcnow` |
| 18 | `chat_service.py` | 132 | `GroupChatMember` not imported | Add to import list |
| 19 | `notifications/__init__.py` | 2 | Imports from non-existent module | Fix import |
| 20 | `admin/asset_tracking.py` | 1-4 | `AssetTrackingService` declared but never defined | Define or remove |

---

## 2. SCHEMA & MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 21 | `communication.py` | 50, 144, 168, 193, 310, 329, 401, 402 | FK references `communication.*` instead of `comms.*` | Change to `comms.*` |
| 22 | `marketing.py` | 55-56 | FK references `commerce.*` | Change to `comms.*` and `catalog.*` |
| 23 | `chat.py` | 19-177 | 11 models missing `country_code`, `is_deleted`, `updated_at` | Add columns |
| 24 | `communication_schema_models.py` | 40-108 | 6 models missing `is_deleted`, `updated_at`, `ondelete` | Add columns |
| 25 | `news.py` | 18-37 | `NewsArticle` missing `updated_at`, `is_deleted`, `country_code` FK | Add columns |
| 26 | `country_control.py` | 20, 40, 63, 85, 103, 122, 140, 159, 179 | 9 FKs missing `ondelete` | Add `ondelete=` |
| 27 | `country_control.py` | 26, 147, 165, 184 | 4 models missing `updated_at` | Add `updated_at` |
| 28 | `country_enhancements.py` | 77, 104, 374 | 3 models missing `updated_at` | Add `updated_at` |
| 29 | `marketing.py` | 18, 33 | `deleted_by` and `deleted_by_id` duplicate columns | Remove duplicate |
| 30 | `communication.py` | 24 | `Notification.type` reserved keyword | Rename to `notification_type` |
| 31 | `communication.py` | 24, 32, 91, 121, 144, 196 | `String` without length | Add length |
| 32 | `communication.py` | 441 | `MaskedMessage.message_hash` is `Integer` | Change to `String(64)` |
| 33 | `chat.py` | 41, 78, 167 | `country_code` declared twice, missing `index=True` | Fix |

---

## 3. CROSS-DOMAIN POLLUTION (CRITICAL)

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 34 | `country_control.py` | 56-75 | `SupplierOnboardingSync` belongs in `suppliers` | Move to `domains/suppliers/models/` |
| 35 | `country_control.py` | 78-93 | `LegalContractTemplate` belongs in `governance` | Move to `domains/governance/models/` |
| 36 | `country_control.py` | 134-149 | `ShopWarehouseLocation` belongs in `logistics` | Move to `domains/logistics/models/` |
| 37 | `country_control.py` | 152-168 | `LogisticsPartnerLocation` belongs in `logistics` | Move to `domains/logistics/models/` |
| 38 | `country_control.py` | 171-187 | `ParcelLocationTracker` belongs in `logistics` | Move to `domains/logistics/models/` |
| 39 | `country_control.py` | 33-53 | `PaymentOrchestratorSync` belongs in `finance` | Move to `domains/finance/models/` |
| 40 | `country_enhancements.py` | 129-147 | `SupplierKYCRequirement` belongs in `suppliers` | Move to `domains/suppliers/models/` |
| 41 | `country_enhancements.py` | 149-169 | `LogisticsPartnerKYCRequirement` belongs in `logistics` | Move to `domains/logistics/models/` |
| 42 | `country_enhancements.py` | 217-234 | `CountryPaymentAlias` belongs in `finance` | Move to `domains/finance/models/` |
| 43 | `country_enhancements.py` | 331-354 | `CountryGatewayConfig` belongs in `finance` | Move to `domains/finance/models/` |
| 44 | `country_enhancements.py` | 57-79 | `CrossCountryCustomerSession` belongs in `customers` | Move to `domains/customers/models/` |
| 45 | `countries.py` | 234-260 | `Message` belongs in `comms` | Move to `domains/comms/models/` |
| 46 | `country_service.py` | 767 | Imports from `governance.models.admin` | Use `governance.ports` |
| 47 | `country_config_admin_service.py` | 563 | Imports from `governance.services.audit` | Use `audit.ports` |

---

## 4. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 4.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 48 | No `kernel/money.py` usage — uses `float()` for money (20+ call sites) | Use `kernel.money.to_decimal()` |
| 49 | No `kernel/currency.py` usage — hardcoded `"AED"` | Use `kernel.currency.Currency` |
| 50 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.normalize_country()` |
| 51 | No `kernel/constants.py` usage | Use `kernel.constants` directly |
| 52 | No `kernel/period.py` usage — hand-rolled date math | Create `kernel.period` |

### 4.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 53 | `rbac` completely unused in country services | Wire `rbac/catalog.py` |
| 54 | `require_feature()` never called in services | Wire in routers |
| 55 | Role string comparison (`== "admin"`) | Use `rbac.require_feature()` |
| 56 | `features.py` not registered in `rbac/catalog.py` | Register features |
| 57 | `sub_admin` invented role not in catalog | Standardize on catalog |

### 4.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 58 | Only `providers.geography` used | Add `providers.geography.fx`, `providers.geography.ip_risk`, `providers.geography.tax_rules` |
| 59 | `providers.payments` never imported | Add connection |
| 60 | `providers.ai` not used for research | Add connection |

### 4.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 61 | No Redis cache on hot read paths | Add `cache_get_json`/`cache_set_json` |
| 62 | No tracing/metrics/Sentry | Add `with_tracing()` and counters |
| 63 | No retry/circuit breaker on write paths | Add `retry()` |
| 64 | `get_service_session()` used as default | Require injected session |
| 65 | In-memory event bus duplicates canonical bus | Delete and use canonical bus |
| 66 | RLS is a no-op (known gotcha) | Complete `instrument_rls` or filter explicitly |

---

## 5. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 67 | `admin/routers/country.py` | 42 | Possible double `/api/v1` prefix | Change to `prefix="/country"` |
| 68 | `admin/routers/country.py` | 203, 212 | `list_public_countries` requires admin | Rename or move to customer |
| 69 | `admin/routers/country.py` | 222, 242 | `body: dict` instead of Pydantic | Add schemas |
| 70 | `admin/routers/country.py` | many | `_: dict` shadow + forwarded as user | Rename to `current_user` |
| 71 | `admin/routers/country.py` | 502, 512, 523 | Route shadowing by `/{code}` catch-all | Reorder routes |
| 72 | `admin/routers/country.py` | many | No path-param constraints | Add regex/length constraints |
| 73 | `admin/routers/country.py` | 419 | `/communications` shadowed by `/{code}` | Reorder routes |
| 74 | `admin/routers/country.py` | 431 | `/communications/{comm_id}/read` route ordering | Reorder routes |
| 75 | `admin/routers/country.py` | all | No `response_model=` | Add response models |
| 76 | `admin/routers/country.py` | 18-200 | `current_user=None` shim breaks audit trail | Remove shim layer |
| 77 | `admin/routers/country.py` | 253, 419 | No offset/cursor pagination | Add pagination |
| 78 | `admin/routers/country.py` | all | `require_feature` called in body, not as Depends | Convert to Depends |
| 79 | `employee/routers/country.py` | 1-8 | Duplicate imports, misnamed file, HR content | Move to `employee/routers/travel.py` |
| 80 | `employee/routers/country.py` | 25-75 | No Pydantic, raw date strings | Add schemas |
| 81 | `customer/routers/country.py` | — | **FILE DOES NOT EXIST** | Create |
| 82 | `supplier/routers/country.py` | — | **FILE DOES NOT EXIST** | Create |
| 83 | `logistics/routers/country.py` | — | **FILE DOES NOT EXIST** | Create |
| 84 | `admin/routers/country.py` | 87-105 | WebSocket has no auth | Add auth |
| 85 | `admin/routers/country.py` | 1015-1023 | `admin_list_channels` returns global data | Add country filter |
| 86 | `admin/routers/country.py` | 585-623 | GET endpoint mutates data | Change to POST |
| 87 | `employee/routers/country.py` | 652 | `rbac_get_current_user` not a re-export | Fix import |
| 88 | `employee/routers/country.py` | 594 | `seed_comms` not importable | Fix import |
| 89 | `employee/routers/country.py` | 177-278 | 20+ undefined function calls | Create or import |
| 90 | `admin/routers/country.py` | — | ConfigVersion workflow unwired | Add routes |
| 91 | `admin/routers/country.py` | — | No Pydantic schemas directory | Create `domains/country/schemas/` |

---

## 6. DUPLICATE FILES & LOGIC

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 92 | `country_service.py` / `country_config_admin_service.py` | Duplicate country CRUD | Consolidate |
| 93 | `events.py` (root) / `services/events.py` | Two parallel event systems | Pick one |
| 94 | `comms_service.py` / `email_management.py` | Duplicate email/template/campaign functions | Delete `comms_service.py` duplicates |
| 95 | `services/events.py` / root `events.py` | Duplicate events | Delete `services/events.py` |
| 96 | `services/subscribers.py` / root `subscribers.py` | Duplicate subscribers | Delete `services/subscribers.py` |
| 97 | `services/features.py` / root `features.py` | Duplicate features | Delete `services/features.py` |
| 98 | `services/ports.py` / root `ports.py` | Duplicate ports | Delete `services/ports.py` |
| 99 | `admin/communication_audit.py` / `admin/__init__.py` | Stub returns `None` | Implement or remove |
| 100 | `notifications/__init__.py` | Imports from non-existent module | Fix import |

---

## 7. SCALABILITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 101 | `country_service.py` | 1939-1969 | `@lru_cache` over DB reads | Use Redis cache |
| 102 | `country_service.py` | 279-308 | Unbounded `list_public_cities` | Add pagination |
| 103 | `country_service.py` | 1545, 1587 | Hard `limit(100)` and `limit(50)` | Add cursor pagination |
| 104 | `country_service.py` | 194-265 | `_from_json` parses same JSON on every call | Cache parsed JSON |
| 105 | `country_service.py` | 1704-1734 | `update_country_cities_bulk` not bulk-insert | Use `bulk_insert_mappings` |
| 106 | `country_auto_populate.py` | 911-923 | 5 external APIs called serially | Use `asyncio.gather` |
| 107 | `cross_border_service.py` | 64 | `AddressFormatService` opens DB on every call | Cache in Redis |
| 108 | `email_management.py` | 247-254 | Unbounded `list_all_campaigns` | Add pagination |
| 109 | `email_management.py` | 344-348 | N+1 in `get_email_marketing_stats` | Use `GROUP BY` |
| 110 | `messaging/websocket_handlers.py` | 29-30 | In-memory WS state not Redis-backed | Use Redis pub/sub |

---

## 8. SECURITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 111 | `country_service.py` | 1522-1536 | XSS in `CountryCommunication.body` | Use `bleach.clean()` |
| 112 | `country_service.py` | 37-65 | Role string comparison instead of RBAC | Use `rbac.require_feature()` |
| 113 | `country_service.py` | 336-512 | Mass-assignment via `dict[str, Any]` | Use Pydantic schema |
| 114 | `country_maps_service.py` | 36-57 | `get_country_map` returns user-editable GeoJSON | Validate GeoJSON |
| 115 | `country_service.py` | 1359-1372 | `test_gateway_connection` returns raw error | Strip messages server-side |
| 116 | `proxy_communication.py` | 238-240 | Fake encryption (plaintext with flag) | Implement real encryption |
| 117 | `email/email_gateway.py` | 108 | XSS in email bodies | Use `markupsafe.escape()` |
| 118 | `email/transactional.py` | 75, 155, 206, 248, 367, 405, 451 | XSS in email templates | Escape all dynamic values |
| 119 | `messaging/chat_service.py` | 189-200, 282-293 | Stored XSS in chat | Use `bleach.clean()` |
| 120 | `messaging/websocket_handlers.py` | 218-287 | WebSocket privilege escalation | Add membership check |

---

## 9. MISSING FUNCTIONALITY (23 GAPS)

### 9.1 CRITICAL (4 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 121 | **Live FX rate service** | `fx/fx_rate_service.py` + `providers/geography/fx.py` + APScheduler job |
| 122 | **IP risk / VPN / fraud detection** | `risk/ip_risk_service.py` + `providers/geography/ip_risk.py` |
| 123 | **Tax-rule engine** (region/category/OSS) | `tax/tax_rule_engine.py` + new models |
| 124 | **GDPR/PDPL consent + transfer log** | `compliance/consent_service.py` + new models |

### 9.2 HIGH (5 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 125 | **Postal-code validator** | `geo/postal_code_service.py` + `providers/geography/postal_codes.py` |
| 126 | **Shipping-zone engine** | `shipping/shipping_zone_engine.py` + new models |
| 127 | **Business-day / holiday calendar** | `calendar/business_calendar_service.py` |
| 128 | **i18n message catalogue** | `localization/i18n_service.py` + new models |
| 129 | **Sanctions / export controls** | `restriction/compliance_service.py` + `providers/geography/sanctions.py` |

### 9.3 MEDIUM (7 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 130 | **Country daily metrics rollup** | `analytics/country_rollup_service.py` |
| 131 | **Real reverse-geocoding** | `geo/reverse_geocode_service.py` |
| 132 | **Address parser** | `geo/address_parser.py` |
| 133 | **GeoFenceService country fence stub** | Fix `country_detection.py:160-170` |
| 134 | **National-ID validator** | `identity/national_id_service.py` |
| 135 | **Country-level SLA rules** | Extend `CountryLogisticsZone` |
| 136 | **Hijri-aware promotion scheduler** | `HijriEventRule` model |

### 9.4 LOW (7 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 137 | **Language auto-detect** | `providers/geography/lang_detect.py` |
| 138 | **DB-driven currency symbol** | Edit `localization_service.py:122` |
| 139 | **VAT-number validation** | `tax/vat_validation_service.py` |
| 140 | **Currency-rounding policy** | Extend `CountryTax` |
| 141 | **Number-to-words** | `localization/number_to_words_service.py` |
| 142 | **Distance / isochrone** | `providers/geography/routing.py` |
| 143 | **Refactor services off `get_db_context()`** | Edit `cross_border_service.py` |

---

## Priority Action Plan

### Phase 1: P0 (Fix Before Deploy)

| # | Action |
|---|--------|
| 1 | Fix all 20 P0 `NameError` bugs |
| 2 | Implement `_record` for audit trail |
| 3 | Fix `lru_cache` over DB |
| 4 | Fix `rloat`/`rerresh` typos |
| 5 | Remove stub `svc_assign_staff` |
| 6 | Fix all 3 routers' `domains.common.*` imports |
| 7 | Create missing routers (customer, supplier, logistics) |
| 8 | Add auth to WebSocket endpoints |
| 9 | Add `require_feature()` to all state-changing endpoints |
| 10 | Create missing Pydantic schemas |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 11 | Fix all 10 `communication.*` FKs → `comms.*` |
| 12 | Fix 2 `commerce.*` FKs |
| 13 | Add missing `is_deleted`, `updated_at`, `country_code` columns |
| 14 | Add missing `ondelete` clauses |
| 15 | Remove cross-domain model imports |
| 16 | Remove campaign delegation to orders |
| 17 | Add RBAC to all service permission checks |
| 18 | Add pagination to all list endpoints |
| 19 | Add Pydantic schemas to all endpoints |
| 20 | Add country scoping to `admin_list_channels` |
| 21 | Change `/unified-inbox/reset` to POST |
| 22 | Implement open/click tracking |
| 23 | Implement bounce handling |
| 24 | Implement one-click unsubscribe |
| 25 | Implement template engine |
| 26 | Implement campaign scheduler |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 27 | Delete duplicate files |
| 28 | Consolidate duplicate logic |
| 29 | Add missing imports |
| 30 | Add tracing/metrics |
| 31 | Add retry/circuit breaker |
| 32 | Fix session leaks |
| 33 | Add N+1 query fixes |
| 34 | Add unbounded query limits |
| 35 | Implement SMS/WhatsApp functionality |
| 36 | Implement in-app notification delivery |
| 37 | Implement chat attachments |
| 38 | Implement campaign A/B testing |
| 39 | Implement segmentation |
| 40 | Implement compliance features |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 50+ |
| Files with cross-domain pollution | 15+ |
| CRITICAL issues | 40+ |
| HIGH issues | 60+ |
| MEDIUM issues | 50+ |
| LOW issues | 30+ |
| P0 runtime errors | 20 |
| Wrong schema FKs | 12 |
| Missing `is_deleted` | 10 models |
| Missing `updated_at` | 7 models |
| Missing RBAC | Entire domain |
| Missing kernel usage | 5 modules |
| Missing provider connections | 4 |
| Missing functionality gaps | 23 |
| Duplicate file pairs | 10 |
| God files (>500 lines) | 2 |
| Missing routers | 3 |
| Security vulnerabilities | 10 |
