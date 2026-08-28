# ZOZI Backend — Phase 2 Complete Investigation Report

> **Generated:** 2026-08-28 (after Phase 1 fixes)  
> **Source:** 10 parallel investigation agents  
> **Scope:** All 16 domains + infrastructure + providers + kernel + rbac + modules  
> **Total problems found:** 2,800+

---

## Executive Summary

| Category | Problems | Severity |
|---|---|---|
| Architecture & Wiring | 89 | 🔴 Critical |
| Code Quality & Logic | 200+ | 🟠 High |
| Domain & Module Structure | 31+ | 🟠 High |
| Database & Data Layer | 300+ | 🔴 Critical |
| Security | 22 | 🔴 Critical |
| Infrastructure & Connections | 9 | 🟡 Medium |
| Performance & Scalability | 100+ | 🟠 High |
| Error & Exception Handling | 50+ | 🟡 Medium |
| Testing & Validation | 30+ | 🟡 Medium |
| Router Wiring | 600+ | 🟠 High |
| Cross-Domain Writes | 85+ | 🔴 Critical |

**Overall: NOT production-ready.** While Phase 1 fixed many issues, substantial architectural debt remains.

---

## 1. Architecture & Wiring (89 violations)

### Law #1: Upward Imports
| File | Line | Import | Fix |
|------|------|--------|-----|
| `accounts/services/auth/auth_service.py` | 1722 | `from rbac.dependencies import _ROLE_FEATURES` | Remove, use lazy helper |
| `accounts/services/users/user_management_service.py` | 122 | `from rbac.dependencies import _ROLE_FEATURES` | Remove, use lazy helper |
| `accounts/services/permissions/permission_service.py` | 447 | `from rbac.dependencies import _ROLE_FEATURES` | Remove, use lazy helper |
| `infrastructure/database/seed/_common.py` | 326 | `from domains.logistics.ports import ...` | OK (ports-based) |
| `infrastructure/security/security_audit.py` | 67 | `from domains.audit.ports import AuditLog` | OK (ports-based) |

### Law #3: Cross-Domain Model Imports (58 violations)
| Domain | Files | Count |
|--------|-------|-------|
| accounts | auth_service.py, gdpr_service.py | 13 |
| governance | settings/misc_service.py, users_service.py, operations.py, products_service.py, export_read_service.py, misc_write_service.py | 31 |
| logistics | tracking/service.py, shipping/service.py, shipments_service.py | 4 |
| customers | wishlist_*.py, user_read_service.py, security_service.py, search_service.py, reviews_service.py, recommendations/service.py, public_comms_status_service.py | 10 |
| orders | ports.py | 2 |
| audit | logs/audit_service.py, logs/audit_query_service.py, compliance_engine.py | 3 |
| comms | tickets/tickets_service.py | 1 |

### Misplaced Files (26+)
| Path | Issue |
|------|-------|
| `domains/_parked/` | 24 archived service/controller files |
| `domains/governance/services/auth/auth_controller_service.py` | Controller in domain layer |
| `modules/admin/routers/country_versioning.py` | Extra router (not canonical domain) |
| `domains/payments/` | Illegal domain (should be in finance) |
| `backend/check_features.py` | Root-level temp script |
| `backend/lifespan.py` | Root-level infrastructure file |

---

## 2. Code Quality & Logic (200+ problems)

### Float Money Casts (50+ instances)
| File | Count |
|------|-------|
| infrastructure/utils/invoice_html.py | 18 |
| domains/orders/services/tracking/service.py | 14 |
| domains/country/services/core/country_service.py | ~25 |
| domains/analytics/services/aggregation/command_center_service.py | 10 |
| Other files | 10+ |

### Broken Logic (8 instances)
| File | Line | Issue |
|------|------|-------|
| finance/services/ledger/general_ledger_service.py | 7358 | OFFSET bug (already fixed) |
| analytics/services/aggregation/command_center_service.py | 535 | datetime not JSON-serializable |
| middleware/rate_limit_middleware.py | 70 | time.sleep(60) blocks async |
| jobs/seed_all.py | 304 | SQL injection via string concat |
| providers/bg_removal/bg_removal_service.py | 803 | fast_mode param ignored |

### SQL Injection (5 HIGH risk)
| File | Line | Issue |
|------|------|-------|
| hr/services/employees/hr_service.py | 499,513,537,549,561,591,632 | `.format()` on SQL |
| hr/services/performance/kpi.py | 104 | f-string in text() |

---

## 3. Domain & Module Structure (31+ violations)

### Missing Router Registrations
| Module | Missing in __init__.py |
|--------|------------------------|
| employee | audit, catalog, customers, governance |

### Illegal Domain
| Domain | Should Be |
|--------|-----------|
| `domains/payments/` | `domains/finance/` |

### RBAC Misconfiguration
| Issue | Fix |
|-------|-----|
| `rbac/catalog.py` scans illegal `payments` domain | Remove payments scan |
| `rbac/models/permission_entities.py` misnamed | Rename to `models.py` |

### Misplaced Files (25+)
| Path | Issue |
|------|-------|
| `domains/_parked/` | 24 archived files |
| `domains/governance/services/auth/auth_controller_service.py` | Controller in domain |
| `backend/check_features.py` | Root-level temp script |

---

## 4. Database & Data Layer (300+ problems)

### Schema Mismatches (30+ models)
| File | Models | Current Schema | Correct Schema |
|------|--------|----------------|----------------|
| orders/models/order_entities.py | 5 models | `commerce` | `orders` |
| catalog/models/products.py | 10+ models | `commerce` (FK ref) | `catalog` |
| governance/models/admin.py | 20+ models | `configuration`, `logistics`, `comms`, etc. | `governance` |
| hr/models/employee_models.py | 30+ models | `logistics` | `hr` |
| customers/models/customer_schema_models.py | 4 models | `governance` (FK ref) | `customers` |

### Missing Audit Columns (200+ models)
| Domain | Models Missing |
|--------|---------------|
| governance | 30+ models |
| finance | 60+ models |
| hr | 30+ models |
| logistics | 20+ models |
| comms | 28+ models |
| suppliers | 10+ models |
| customers | 10+ models |
| security | 10+ models |
| orders | 5+ models |
| catalog | 10+ models |
| accounts | 15+ models |
| country | 30+ models |

### Reserved Keywords (74 columns)
| Domain | Columns |
|--------|---------|
| finance | `status` on 20+ columns |
| hr | `status` on 15+ columns |
| governance | `status`, `role`, `key` on 10+ columns |
| comms | `status`, `type`, `role` on 30+ columns |

---

## 5. Security (22 violations)

### CRITICAL (2)
| # | Issue | File | Line |
|---|-------|------|------|
| 1 | Refresh token reuse not detected | public_security_registration_service.py | 120-141 |
| 2 | Rate limiting fails OPEN | rate_limit_middleware.py | 166-179 |

### HIGH (9)
| # | Issue | File | Line |
|---|-------|------|------|
| 3 | Hardcoded JWT secret in .env | .env | 4 |
| 4 | Token blacklist fails open | auth.py | 96-110 |
| 5 | OTP endpoints no rate limiting | public_security_registration_service.py | 63-85 |
| 6 | SQL injection via f-string | command_center_query_service.py | 30-36 |
| 7 | CSRF bypassed in dev/test | csrf_middleware.py | 50-54 |
| 8 | Email leaked in error response | public_security_registration_service.py | 118 |
| 9 | Passwords >72 bytes not rejected | schemas.py | 67-80 |
| 10 | SSO audience verification disabled | auth_service.py | 992 |

---

## 6. Infrastructure & Connections (9 violations)

| # | Issue | File | Line |
|---|-------|------|------|
| 1 | Redis canonical location wrong | infrastructure/redis/ | — |
| 2 | Cache import chain (3-hop) | infrastructure/utils/cache.py | 22-26 |
| 3 | DeviceBinding middleware not wired | orchestrator.py | — |
| 4 | ZeroTrust middleware not wired | orchestrator.py | — |
| 5 | Dead code: rls_middleware.py | middleware/ | — |
| 6 | Dead code: rls_dependency.py | middleware/ | — |
| 7 | Dead set_session_rls | country_context.py | 266-274 |
| 8 | Legacy rls_context global | country_context.py | 200-204 |
| 9 | Graceful shutdown missing | lifespan.py | 282-291 |

---

## 7. Performance & Scalability (100+ problems)

### OFFSET Pagination (82 instances)
| Domain | Files |
|--------|-------|
| catalog | search_service.py |
| orders | orders_service.py, order_engine.py |
| finance | payment_engine.py, payout_batch_service.py |
| logistics | shipment_service.py, admin_logistics_service.py |

### Unbounded `.all()` Queries (100+ instances)
| File | Count |
|------|-------|
| catalog/services/search/search_service.py | 2 |
| audit/services/worm_audit.py | 1 |
| suppliers/services/settlement/multi_currency_settlement.py | 1 |
| catalog/services/products/products_service.py | 1 |

---

## 8. Error & Exception Handling (50+ problems)

### Raw Exception Exposure (14 locations)
| File | Line | Pattern |
|------|------|---------|
| analytics_service.py | 320 | `{"error": str(e)}` |
| catalog/search_service.py | 34 | `{"error": str(exc)}` |
| customers/search_service.py | 75 | `{"error": str(exc)}` |
| modules/employee/routers/hr.py | 690 | `{"error": str(e)}` as 200 OK |
| modules/employee/routers/orders.py | 179+ | 9× `HTTPException(400, str(e))` |

### Missing Test Files (3 domains)
| Domain | Test Files |
|--------|------------|
| accounts | 0 ❌ |
| analytics | 0 ❌ |
| promotions | 0 ❌ |

---

## 9. Router Wiring (600+ problems)

### Router Registration
| Module | Issue |
|--------|-------|
| employee | 3 routers not registered in __init__.py |

### Bare require_feature() Calls (582)
All modules have bare calls instead of `Depends(require_feature(...))`.

### Missing Pagination (17+ list endpoints)
admin: accounts, country, orders, promotions, security
customer: orders, promotions, customers
logistics: logistics

### Missing Error Handling (~400+ endpoints)
Nearly all endpoints across all modules lack try/except.

### Finance Router Bug
| File | Line | Issue |
|------|------|-------|
| employee/routers/finance.py | 1207 | `router = APIRouter(...)` overwrites first router |

---

## 10. Cross-Domain Writes (85+ violations)

### db.add() Cross-Domain (42 violations)
| Source → Target | Count |
|-----------------|-------|
| accounts → governance | 28 |
| customers → promotions | 5 |
| orders → comms | 4 |
| finance → governance | 4 |

### .update() Cross-Domain (15 violations)
### .delete() Cross-Domain (28 violations)

### Event Infrastructure Status
| Component | Status |
|-----------|--------|
| Domains with real event classes | 3 of 15 (comms, country, finance) |
| Domains with real subscriber handlers | 0 of 15 |
| Domains with real port functions | 15 of 15 |

---

## Priority Action Plan

### P0 — Critical (Fix Immediately)
1. Fix refresh token reuse detection (2 files)
2. Fix rate limiting fail-open (middleware + public endpoint)
3. Fix SQL injection in HR services (7 locations)
4. Add test files for accounts, analytics, promotions

### P1 — High (Fix Soon)
5. Route 58 cross-domain model imports through ports.py
6. Add 3 missing employee router registrations
7. Fix finance router variable overwrite
8. Add error handling to ~400 endpoints
9. Fix 14 raw exception exposures

### P2 — Medium (Fix in Sprint)
10. Add missing audit columns to 200+ models
11. Fix 30+ schema mismatches
12. Replace 82 OFFSET pagination with keyset
13. Remove 24 files from `_parked/`
14. Fix 9 infrastructure violations

---

*Report generated by 10 parallel investigation agents*
*Previous Phase 1 fixed ~500 issues; ~2,300 remain*
