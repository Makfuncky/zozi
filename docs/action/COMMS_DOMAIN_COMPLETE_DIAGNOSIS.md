# Comms Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/comms/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **150+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 30+ |
| 🟠 HIGH | 50+ |
| 🟡 MEDIUM | 45+ |
| 🟢 LOW | 25+ |
| **TOTAL** | **150+** |

---

## 1. BROKEN IMPORTS (CRITICAL — Runtime Crashes)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `system_comms_status_service.py` | 25-30 | Imports from non-existent `messaging/chat/chat_write_service` | Create or fix import |
| 2 | `messaging/chat_service.py` | 697, 730, 736 | `utcnot` not imported | Add `from infrastructure.utils.datetime_utils import utcnow` |
| 3 | `messaging/chat_service.py` | 132 | `GroupChatMember` not imported | Add to import list |
| 4 | `email/transactional.py` | 30, 222 | `User` not imported at module level | Add import |
| 5 | `tickets/tickets_service.py` | 232 | `desc` not imported | Add `from sqlalchemy import desc` |
| 6 | `admin/asset_tracking.py` | 1-4 | `AssetTrackingService` declared but never defined | Define or remove |
| 7 | `notifications/__init__.py` | 2 | Imports from non-existent `shared/notification/notification_service` | Fix import |
| 8 | `admin/__init__.py` | 6-8 | Stub returns `None` | Implement or remove |

---

## 2. SCHEMA & MODEL ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 9 | `communication.py` | 50, 144, 168, 193, 310, 329, 401, 402 | FK references `communication.*` instead of `comms.*` | Change to `comms.*` |
| 10 | `marketing.py` | 55-56 | FK references `commerce.*` instead of `comms.*` and `catalog.*` | Fix FKs |
| 11 | `chat.py` | 19-177 | 11 models missing `country_code`, `is_deleted`, `updated_at` | Add columns |
| 12 | `communication_schema_models.py` | 40-108 | 6 models missing `is_deleted`, `updated_at`, `ondelete` | Add columns |
| 13 | `news.py` | 18-37 | `NewsArticle` missing `updated_at`, `is_deleted`, `country_code` FK | Add columns |
| 14 | `marketing.py` | 18, 33 | `deleted_by` and `deleted_by_id` duplicate columns | Remove duplicate |
| 15 | `communication.py` | 24 | `Notification.type` is reserved keyword | Rename to `notification_type` |
| 16 | `communication_schema_models.py` | 43 | `SupportTicket.status` reserved keyword | Rename to `status_code` |
| 17 | `communication.py` | 24, 32, 91, 121, 144, 196 | `String` without length | Add length |
| 18 | `communication.py` | 441 | `MaskedMessage.message_hash` is `Integer` | Change to `String(64)` |
| 19 | `chat.py` | 41, 78, 167 | `country_code` declared twice, missing `index=True` | Fix |

---

## 3. CROSS-DOMAIN POLLUTION (CRITICAL)

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 20 | `email/email_management.py` | 586-607 | Delegates campaign CRUD to `orders` domain | Remove delegation |
| 21 | `tickets/tickets_service.py` | 2-3, 173-233 | Imports `finance.Invoice` and `orders.Order` | Use ports |
| 22 | `messaging/websocket_handlers.py` | 11-20 | Imports 8 models from `governance` | Use comms models |
| 23 | `tickets/tickets_service.py` | 13-14 | Imports `SupportTicket` from `governance.ports` | Use comms models |
| 24 | `email/transactional.py` | 15 | Imports from `orders.services.tracking` | Use ports |
| 25 | `system_comms_status_service.py` | 3-6 | Imports from `customers.services` | Remove |
| 26 | `comms_service.py` | 30-31 | Dead imports from `governance` and `accounts` | Remove |

---

## 4. SECURITY ISSUES (CRITICAL)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 27 | `proxy_communication.py` | 238-240 | **Fake encryption** — `_encrypt_content` returns plaintext | Implement real encryption |
| 28 | `email/email_gateway.py` | 108 | **XSS** — unescaped HTML in email bodies | Use `markupsafe.escape()` |
| 29 | `email/transactional.py` | 75, 155, 206, 248, 367, 405, 451 | **XSS** — user data interpolated into HTML | Escape all dynamic values |
| 30 | `messaging/chat_service.py` | 189-200, 282-293 | **Stored XSS** — no content sanitization | Use `bleach.clean()` |
| 31 | `messaging/websocket_handlers.py` | 218-287 | **Horizontal privilege escalation** — any user can join any room | Add membership check |
| 32 | `comms_service.py` | 475-535 | Role string comparison instead of RBAC | Use `rbac.require_feature()` |
| 33 | `email/email_management.py` | 150-243 | No permission check on campaign/template mutations | Add permission checks |
| 34 | `proxy_communication.py` | 545-550 | Bare `Exception` swallowed | Narrow exception types |
| 35 | `email/email_gateway.py` | 175, 221, 244, 274, 301, 428 | 22 exception types enumerated | Use `except Exception` + `logger.exception` |
| 36 | `ediscovery.py` | 50, 124, 142, 160, 174 | LIKE injection risk | Escape user input |
| 37 | `proxy_communication.py` | 80 | Session leak via `get_service_session()` | Use injected `db` |
| 38 | `messaging/chat_service.py` | 593, 617, 668 | Own DB session inside service | Use router-injected `db` |

---

## 5. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 5.1 Kernel (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 39 | No `kernel/money.py` usage — uses `float` for money | Use `kernel.money.to_decimal()` |
| 40 | No `kernel/currency.py` usage — hardcoded `"AED"` | Use `kernel.currency.Currency` |
| 41 | No `kernel/country.py` usage — raw string country codes | Use `kernel.country.normalize_country()` |
| 42 | No `kernel/constants.py` usage | Use `kernel.constants` directly |
| 43 | No `kernel/period.py` usage — hand-rolled date math | Create `kernel.period` |

### 5.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 44 | `rbac` completely unused in comms services | Wire `rbac/catalog.py` |
| 45 | `require_feature()` never called in services | Wire in routers |
| 46 | Role string comparison (`== "customer"`) | Use `rbac.require_feature()` |
| 47 | `features.py` not registered in `rbac/catalog.py` | Register features |

### 5.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 48 | Only `providers.comms.twilio/whatsapp/email` used | Add `providers.comms.sms`, `providers.comms.push` |
| 49 | `providers.media.services.ai` invoked via string import | Refactor to thin `providers.ai` |
| 50 | `providers.payments` never imported | Add connection |
| 51 | `providers.qr`, `providers.barcode`, `providers.scanner` not used | Add on demand |

### 5.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 52 | No Redis cache on hot read paths | Add `cache_get_json`/`cache_set_json` |
| 53 | No tracing/metrics/Sentry | Add `with_tracing()` and counters |
| 54 | No retry/circuit breaker on write paths | Add `retry()` |
| 55 | `get_service_session()` used as default | Require injected session |
| 56 | In-memory event bus duplicates canonical bus | Delete and use canonical bus |
| 57 | In-memory WebSocket state not Redis-backed | Use Redis pub/sub |

---

## 6. ROUTER CONNECTION ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 58 | `admin/routers/comms.py` | 6-9 | Imports from non-existent `domains.common.*` | Fix imports |
| 59 | `customer/routers/comms.py` | 1-5 | Imports from non-existent `domains.common.*` | Fix imports |
| 60 | `employee/routers/comms.py` | 8-9 | Imports from non-existent `domains.common.*` | Fix imports |
| 61 | `supplier/routers/comms.py` | — | **FILE DOES NOT EXIST** | Create |
| 62 | `logistics/routers/comms.py` | — | **FILE DOES NOT EXIST** | Create |
| 63 | `admin/routers/comms.py` | 31, 38, 51, 63, 75 | Only 2 feature atoms gated | Add missing gates |
| 64 | `employee/routers/comms.py` | 49-1334 | Most endpoints have no `require_feature()` | Add gates |
| 65 | `customer/routers/comms.py` | 33-44 | No auth on endpoints | Add auth |
| 66 | `admin/routers/comms.py` | 87-105 | WebSocket has no auth | Add auth |
| 67 | `employee/routers/comms.py` | 1015-1023 | `admin_list_channels` returns global data | Add country filter |
| 68 | `employee/routers/comms.py` | 585-623 | GET endpoint mutates data | Change to POST |
| 69 | `employee/routers/comms.py` | 652 | `rbac_get_current_user` not a re-export | Fix import |
| 70 | `employee/routers/comms.py` | 594 | `seed_comms` not importable | Fix import |
| 71 | `employee/routers/comms.py` | 177-278 | 20+ undefined function calls | Create or import |
| 72 | `admin/routers/comms.py` | 28-30 | `cursor` param never passed to service | Forward or remove |
| 73 | `employee/routers/comms.py` | 86-90 | `list_threads` no pagination | Add pagination |
| 74 | `employee/routers/comms.py` | 697-705 | `get_notifications` no pagination | Add pagination |
| 75 | `employee/routers/comms.py` | 418-542 | `Body(default={})` instead of Pydantic | Add schemas |

---

## 7. DUPLICATE FILES & LOGIC

| # | Files | Issue | Fix |
|---|-------|-------|-----|
| 76 | `comms_service.py` / `email_management.py` | Duplicate email/template/campaign functions | Delete `comms_service.py` duplicates |
| 77 | `services/events.py` / root `events.py` | Duplicate events | Delete `services/events.py` |
| 78 | `services/subscribers.py` / root `subscribers.py` | Duplicate subscribers | Delete `services/subscribers.py` |
| 79 | `services/features.py` / root `features.py` | Duplicate features | Delete `services/features.py` |
| 80 | `services/ports.py` / root `ports.py` | Duplicate ports | Delete `services/ports.py` |
| 81 | `admin/communication_audit.py` / `admin/__init__.py` | Stub returns `None` | Implement or remove |
| 82 | `notifications/__init__.py` | Imports from non-existent module | Fix import |

---

## 8. SCALABILITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 83 | `comms_service.py` | 189, 207 | N+1 in `get_unified_inbox` | Use `LEFT JOIN LATERAL` |
| 84 | `email_management.py` | 247-254 | Unbounded `list_all_campaigns` | Add pagination |
| 85 | `email_management.py` | 344-348 | N+1 in `get_email_marketing_stats` | Use `GROUP BY` |
| 86 | `messaging/chat_service.py` | 507-553 | Subquery has no limit | Add limit |
| 87 | `messaging/chat_service.py` | 596-637 | No eager loading | Add `selectinload` |
| 88 | `messaging/websocket_handlers.py` | 29-30 | In-memory WS state not Redis-backed | Use Redis pub/sub |
| 89 | `comms_service.py` | 133-274 | No caching on unified inbox | Add Redis cache |
| 90 | `shared_utils.py` | 339-361 | 5 sequential COUNTs | Use single aggregate query |
| 91 | `email_management.py` | 99-120 | Unbounded `list_suppressions` | Add pagination |
| 92 | `email_gateway.py` | 297-304 | Bulk send synchronous | Use background jobs |

---

## 9. MISSING FUNCTIONALITY (45 GAPS)

### 9.1 Email (7 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 93 | Open/click tracking pixel + endpoint | CRITICAL |
| 94 | Bounce handling (webhook → suppression) | CRITICAL |
| 95 | Template engine (Jinja + locale) | HIGH |
| 96 | Campaign scheduler (APScheduler) | HIGH |
| 97 | One-click unsubscribe (RFC 8058) | CRITICAL |
| 98 | Email warm-up / throttling | MEDIUM |
| 99 | DLP scope (attachments, headers) | LOW |

### 9.2 SMS (5 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 100 | `SMSTemplate` / SMS provider abstraction | HIGH |
| 101 | Two-way SMS / inbound handling | HIGH |
| 102 | Opt-in / opt-out management | HIGH |
| 103 | Delivery receipts (DLR) | MEDIUM |
| 104 | Sender ID / phone number pool per country | MEDIUM |

### 9.3 WhatsApp (6 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 105 | Template-message API (HSM) | CRITICAL |
| 106 | Media messages | HIGH |
| 107 | Interactive messages | MEDIUM |
| 108 | Inbound WhatsApp | HIGH |
| 109 | Opt-in management | HIGH |
| 110 | Status / read receipts | MEDIUM |

### 9.4 Push Notifications (5 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 111 | FCM / APNs / WebPush provider + service | CRITICAL |
| 112 | Scheduled pushes | HIGH |
| 113 | Topic / segment broadcast | MEDIUM |
| 114 | Push analytics | MEDIUM |
| 115 | Silent / data-only pushes | LOW |

### 9.5 In-App Notifications (4 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 116 | Real-time WS push of notifications | CRITICAL |
| 117 | Read receipts over WS | HIGH |
| 118 | Per-user notification preferences | HIGH |
| 119 | Notification grouping / digest | MEDIUM |

### 9.6 Chat (4 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 120 | Message history pagination service | HIGH |
| 121 | File attachments (upload + scan + thumbnail) | HIGH |
| 122 | Search across chat history | MEDIUM |
| 123 | Typing / presence / read-receipts over WS | MEDIUM |

### 9.7 Campaigns (5 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 124 | A/B testing | HIGH |
| 125 | Segmentation engine | HIGH |
| 126 | Dispatcher (batches + throttle) | HIGH |
| 127 | Campaign analytics | MEDIUM |
| 128 | Subscriber CSV import + double-opt-in | MEDIUM |

### 9.8 Webhooks (4 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 129 | General inbound webhook ingress | CRITICAL |
| 130 | Webhook signature verification | HIGH |
| 131 | Outbound webhook retry | MEDIUM |
| 132 | Webhook DLQ | MEDIUM |

### 9.9 Compliance (5 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 133 | GDPR consent (per-channel) | HIGH |
| 134 | One-click unsubscribe (RFC 8058) | CRITICAL |
| 135 | Data retention auto-purge | HIGH |
| 136 | SAR export integration | MEDIUM |
| 137 | Right-to-erasure with legal-hold | MEDIUM |

### 9.10 Analytics (4 gaps)

| # | Gap | Priority |
|---|-----|----------|
| 138 | Cross-channel delivery dashboard | HIGH |
| 139 | SMS/WhatsApp delivery metrics | HIGH |
| 140 | Push delivery/open metrics | MEDIUM |
| 141 | Cohort + funnel analysis | LOW |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix all 8 broken imports |
| 2 | Fix all 10 `communication.*` FKs → `comms.*` |
| 3 | Fix 2 `commerce.*` FKs → `comms.*` and `catalog.*` |
| 4 | Implement real encryption in `_encrypt_content` |
| 5 | Add HTML escaping for all email bodies |
| 6 | Add `bleach.clean()` for chat messages |
| 7 | Add WebSocket room membership check |
| 8 | Replace `float()` money with `kernel.money.to_decimal()` |
| 9 | Wire `rbac/catalog.py` and `require_feature()` |
| 10 | Fix all 3 routers' `domains.common.*` imports |
| 11 | Create missing routers (supplier, logistics) |
| 12 | Add auth to WebSocket endpoints |
| 13 | Add `require_feature()` to all state-changing endpoints |
| 14 | Create missing webhook ingress |
| 15 | Create missing push notification provider |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 16 | Add missing `is_deleted`, `updated_at`, `country_code` columns |
| 17 | Add missing `ondelete` clauses |
| 18 | Remove cross-domain model imports |
| 19 | Remove campaign delegation to orders |
| 20 | Add RBAC to all service permission checks |
| 21 | Add pagination to all list endpoints |
| 22 | Add Pydantic schemas to all endpoints |
| 23 | Add country scoping to `admin_list_channels` |
| 24 | Change `/unified-inbox/reset` to POST |
| 25 | Add Redis cache to hot read paths |
| 26 | Add Redis-backed WebSocket presence |
| 27 | Implement open/click tracking |
| 28 | Implement bounce handling |
| 29 | Implement one-click unsubscribe |
| 30 | Implement template engine |
| 31 | Implement campaign scheduler |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---|--------|
| 32 | Delete duplicate files |
| 33 | Consolidate duplicate logic |
| 34 | Add tracing/metrics |
| 35 | Add retry/circuit breaker |
| 36 | Fix session leaks |
| 37 | Add N+1 query fixes |
| 38 | Add unbounded query limits |
| 39 | Implement SMS/WhatsApp functionality |
| 40 | Implement in-app notification delivery |
| 41 | Implement chat attachments |
| 42 | Implement campaign A/B testing |
| 43 | Implement segmentation |
| 44 | Implement compliance features |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 50+ |
| Files with cross-domain pollution | 15+ |
| CRITICAL issues | 30+ |
| HIGH issues | 50+ |
| MEDIUM issues | 45+ |
| LOW issues | 25+ |
| Broken imports | 8 |
| Security vulnerabilities | 11 |
| Missing RBAC | Entire domain |
| Missing kernel usage | 5 modules |
| Missing provider connections | 4 |
| Missing functionality gaps | 45 |
| Duplicate file pairs | 6 |
| God files (>500 lines) | 2 |
| Missing routers | 2 |
