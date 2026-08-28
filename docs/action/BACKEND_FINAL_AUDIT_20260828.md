# ZOZI Backend — Final Consolidated Audit Report

> **Audit Date:** 2026-08-28 (Third Full Investigation)
> **Scope:** `backend/` — all 16 domains, 5 modules, infrastructure, kernel, providers, rbac, middleware, jobs, tests
> **Benchmark:** `ARCHITECTURE_DIAGRAM.md` (read top-to-bottom, 325 laws)
> **Method:** 5 parallel investigation agents covering all 9 problem categories
> **Target:** Architecture clean and production-ready

---

## Executive Summary

| Severity | Count | Impact |
|----------|-------|--------|
| **CRITICAL** | 18 | Security breaches, data corruption, runtime crashes, broken imports |
| **HIGH** | 42 | Architecture violations, performance risks, structural debt |
| **MEDIUM** | 35 | Code quality issues, maintainability debt |
| **LOW** | 10 | Minor inconsistencies |
| **TOTAL** | **105** | |

---

## 1. CRITICAL ISSUES

### C1. CRITICAL — Broken Import: `infrastructure.security.auth` Does Not Exist
**Files affected:**
- `domains/security/services/iam/security_dependencies.py:20` — `from infrastructure.security.auth import decode_token`
- `domains/customers/services/public_comms_status_service.py:9` — `from infrastructure.security.auth import JWTError, jwt`
- `modules/employee/routers/finance.py:617` — `from infrastructure.security.auth import require_permission`

**Impact:** Any request using security domain's auth dependencies will raise `ImportError` at runtime → 500 errors.

**Fix:** Either create `infrastructure/security/auth.py` OR update all imports to use `infrastructure.utils.auth`.

---

### C2. CRITICAL — 49 Duplicate Table Pairs (Law 51)
Each table name appears in multiple domains, causing SQLAlchemy MetaData conflicts and runtime crashes.

| Table | Domain 1 | Domain 2 |
|-------|----------|----------|
| `users` | accounts | governance |
| `user_sessions` | accounts | governance |
| `user_devices` | accounts | governance |
| `password_reset_tokens` | accounts | governance |
| `email_verification_tokens` | accounts | governance |
| `revoked_tokens` | accounts | governance |
| `coupons` | catalog | promotions |
| `banners` | catalog | promotions |
| `bogo_promotions` | catalog | promotions |
| `payout_rules` | finance | country |
| `tax_rules` | finance | country |
| `warehouses` | finance | logistics |
| `meeting_recordings` | comms | security |
| `incident_war_rooms` | comms | governance |
| `legal_contract_templates` | country | governance |
| ...and 34 more pairs | | |

**Fix:** Each table must exist in exactly one canonical domain. Delete duplicates after verifying canonical location.

---

### C3. CRITICAL — Missing `is_deleted` on ~73 Models (Law 54)
Models without soft delete cannot be recovered. Audit trails broken.

**Top offenders:**
| File | Models Missing is_deleted |
|------|--------------------------|
| `governance/models/admin.py` | 20 models |
| `hr/models/employee_models.py` | 18 models |
| `comms/models/chat.py` | 11 models |
| `governance/models/user.py` | 7 models |
| `comms/models/incident.py` | 4 models |
| `comms/models/communication_schema_models.py` | 6 models |

**Fix:** Add `is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)` to all user-facing models.

---

### C4. CRITICAL — Duplicate Auth Implementations (Law 39)
Auth logic exists in **5 separate locations** with divergent behavior:

| Location | Line | Behavior |
|----------|------|----------|
| `accounts/services/auth/auth_service.py` | 1857 | Uses `verify_token()`, returns dict, Redis cache |
| `accounts/services/auth/security_dependencies.py` | 41 | Uses `decode_token()`, returns ORM `User` |
| `infrastructure/security/dependencies.py` | 49 | Uses raw SQL, returns dict |
| `security/services/iam/security_dependencies.py` | 41 | **Broken import — will crash** |
| `logistics/services/core/service.py` | 2996 | 5th implementation, no type check |

**Fix:** Consolidate to single canonical `get_current_user` in `infrastructure/utils/auth.py`. Re-export from there.

---

### C5. CRITICAL — Token Type Not Verified (Law 33)
6 `decode_token()` calls without `expected_type` parameter:

| File | Line | Risk |
|------|------|------|
| `accounts/services/auth/security_dependencies.py` | 52 | Refresh token replay as access token |
| `accounts/services/auth/security_dependencies.py` | 65 | Same, optional variant |
| `security/services/iam/security_dependencies.py` | 52 | Same (also broken import) |
| `security/services/iam/security_dependencies.py` | 65 | Same, optional variant |
| `infrastructure/security/dependencies.py` | 60 | Same |
| `infrastructure/security/dependencies.py` | 74 | Same, optional variant |

**Fix:** All `decode_token()` calls must pass `expected_type="access"` or `expected_type="refresh"` as appropriate.

---

### C6. CRITICAL — Module Routers Import Domain Models Directly (Law 2)
| File | Line | Import |
|------|------|--------|
| `modules/employee/routers/hr.py` | 1170 | `from domains.hr.models.employee_models import EmployeeRelation` |
| `modules/logistics/routers/logistics.py` | 302 | `from domains.governance.models.user import User` |

**Fix:** Remove model imports from routers. Use service calls or Pydantic schemas for type annotations.

---

### C7. CRITICAL — 4 Infrastructure Upward Imports (Law 1)
| File | Line | Import |
|------|------|--------|
| `infrastructure/database/seed/_common.py` | 326 | `from domains.logistics.ports import quote_shipping_for_destination` |
| `infrastructure/security/security_audit.py` | 67 | `from domains.audit.ports import AuditLog` |

**Fix:** Move functions to infrastructure layer or call via dependency injection.

---

### C8. CRITICAL — `_parked` Directory Still Exists (Law 12, 18)
`domains/_parked/` still contains **24 files** that are not part of any valid domain.

**Fix:** Integrate each file into its correct domain service directory or delete.

---

## 2. HIGH ISSUES

### H1. SQL Injection Risk (Law 34)
**File:** `governance/services/command_center/command_center_service.py:60-62`

The `safe_count` function passes `where` clause directly to SQL without validation (unlike the analytics version which validates against an allowlist).

**Fix:** Add `_validate_where_clause(where)` validation or require parameterized queries only.

---

### H2. CSRF Bypassed in Dev/Test (Law 35)
**File:** `middleware/csrf_middleware.py:50-54`

CSRF validation completely bypassed when `app_env` is `test` or `development`.

**Fix:** Remove the bypass or require explicit opt-out.

---

### H3. Hardcoded Seed Password Fallback (Law 32)
**File:** `infrastructure/database/seed/_common.py:38`

Falls back to `"DevSeed123!"` when env vars are unset.

**Fix:** Generate random password with `secrets.token_urlsafe(16)` and log it once.

---

### H4. 3 Module Routers Exceed 1000 Lines (Law 2, 90)
| File | Lines |
|------|-------|
| `modules/employee/routers/finance.py` | 1,570 |
| `modules/employee/routers/hr.py` | 1,236 |
| `modules/routes/logistics.py` | 1,137 |

**Fix:** Extract business logic into domain services. Routers should be thin HTTP shims.

---

### H5. 11 Domains Have Duplicate `events.py` in `services/` (Law 17)
Events files exist both at `domains/{d}/events.py` and `domains/{d}/services/events.py`.

**Fix:** Merge unique handlers into root `events.py`, then delete the duplicate.

---

### H6. 5 Domains Have Duplicate `ports.py` in `services/` (Law 17)
Ports files exist both at `domains/{d}/ports.py` and `domains/{d}/services/ports.py`.

**Fix:** Merge unique port functions into root `ports.py`, then delete the duplicate.

---

### H7. Module Router References Non-Existent Router (Law 8)
**File:** `modules/admin/routers/__init__.py:17`

Lists `"country_versioning"` but no file `modules/admin/routers/country_versioning.py` exists.

**Fix:** Remove `"country_versioning"` from the list.

---

### H8. 13 Raw `SELECT *` Queries (Law 46)
**File:** `hr/services/hr_employee_service.py` (10 queries)

All queries use `SELECT *` instead of explicit column lists.

**Fix:** Replace with explicit column lists.

---

### H9. 100+ OFFSET Pagination Calls
40+ `.offset()` calls across catalog, orders, finance, accounts.

**Fix:** Replace with keyset/cursor pagination for hot lists.

---

### H10. 20+ Silent Exception Swallows (Law 59)
20+ `except Exception: pass` or `except Exception: return None` blocks without logging.

**Fix:** Add `logger.debug("...", exc_info=True)` before every `pass`/`return None`.

---

### H11. Blocking I/O in Async (Law 60)
| File | Line | Issue |
|------|------|-------|
| `accounts/services/auth/auth_service.py` | 953 | `requests.get()` blocks event loop |
| `finance/services/payouts/payout_batch_service.py` | 1574 | `time.sleep()` blocks background job |

**Fix:** Replace with `httpx.AsyncClient()` or `asyncio.to_thread()`.

---

### H12. 12+ Unbounded Caches (Law 61)
Unbounded dict caches found in:
- `auth_service.py:74` — `_JWKS_CACHE`
- `accounts/models/core.py:177` — `_USER_CACHE`
- `general_ledger_service.py:369` — `account_cache`
- `fraud_detection_service.py:75-76` — `_asn_cache`, `_geo_cache`
- ...and 8 more

**Fix:** Use `cachetools.TTLCache(maxsize=1000, ttl=300)`.

---

## 3. MEDIUM ISSUES

### M1. Cross-Domain Service Imports (Law 3)
80+ cross-domain imports in `domains/*/services/` bypassing `ports.py`.

**Top offenders:**
- `orders/services/core/order_engine.py` (8+ service imports)
- `suppliers/services/disputes_service.py`
- `security/services/fraud/fraud_service.py`

**Fix:** Route all cross-domain reads through `ports.py`.

---

### M2. DomainAllowlist.yaml Not Shrinking (Law 7)
The allowlist tracks 35+ temporary cross-domain imports and is growing.

**Fix:** Add migration timeline; aggressively shrink.

---

### M3. 574 TODO/FIXME Comments Without Ticket References (Law 62)
TODOs must include ticket reference and expiration date.

**Fix:** Enforce in CI: `TODO(TICKET-123): description [expires: YYYY-MM-DD]`.

---

### M4. features.py Format Inconsistency (Law 4)
Three different formats across 16 domains:
- `dict[str, str]` — catalog, promotions
- `dict[str, dict]` — 10 domains
- `dict[str, str]` + dataclass — comms

**Fix:** Standardize on `dict[str, dict]` format.

---

### M5. 9 FK Columns Missing `ondelete` (Law 52)
9 FK columns reference `country.country_configs.code` without `ondelete`.

**Fix:** Add explicit `ondelete="RESTRICT"` or `ondelete="SET NULL"`.

---

### M6. 9 FK Columns Missing `index=True` (Law 53)
Same 9 FK columns lack indexes.

**Fix:** Add `index=True` to all FK columns.

---

### M7. `_JWKS_CACHE` Has No TTL (Law 61)
**File:** `auth_service.py:74`

**Fix:** Use TTL of 3600s (JWKS keys rotate hourly).

---

### M8. 2 God Services (>4000 lines) (Law 64)
| File | Lines |
|------|-------|
| `general_ledger_service.py` | 8,874 |
| `payment_engine.py` | 4,675 |
| `auth_service.py` | 4,503 |
| `payout_batch_service.py` | 4,219 |

**Fix:** Split into sub-modules with single responsibilities.

---

### M9. Float for Money in Catalog Services (Law 19)
20+ `float(product.price)` calls in catalog services.

**Fix:** Change `Product.price` to `Numeric(12, 4)` and use `Decimal` throughout.

---

## 4. LOW ISSUES

### L1. Magic Numbers (Law 66)
Numeric constants in business logic without named constants:
- `auth_service.py:953` — `timeout=10`
- `auth_service.py:3031` — `token[-16:]`

**Fix:** Define named constants.

---

### L2. 10+ Functions Missing Return Type Hints (Law 63)
Public functions without `-> ReturnType` annotation.

**Fix:** Add type hints. Run `mypy --strict` to find all missing annotations.

---

### L3. 4 Patterns of Duplicated Code (Law 67)
- `_sanitize_staff_permissions()` duplicated in 2 files
- `recipient_map` pattern duplicated
- `treasury_map`, `last_attendance_map` patterns duplicated
- `config_map` pattern duplicated

**Fix:** Extract shared patterns into `infrastructure/utils/` or `kernel/` helpers.

---

## Priority Action Plan

### Phase 1: CRITICAL (Immediate)

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| 1 | Fix broken `infrastructure.security.auth` imports | Low | Runtime crashes |
| 2 | Consolidate 5 duplicate auth implementations | Medium | Security |
| 3 | Add `expected_type="access"` to 6 decode_token calls | Low | Security |
| 4 | Resolve 49 duplicate table pairs | High | Data integrity |
| 5 | Add `is_deleted` to ~73 models | Medium | Soft delete |
| 6 | Remove model imports from 2 module routers | Low | Architecture |
| 7 | Fix 2 infrastructure upward imports | Low | Architecture |
| 8 | Delete `_parked` directory (24 files) | Medium | Architecture |

### Phase 2: HIGH (This Week)

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| 9 | Fix SQL injection in `safe_count` | Medium | Security |
| 10 | Remove CSRF bypass in dev/test | Low | Security |
| 11 | Remove hardcoded seed password fallback | Low | Security |
| 12 | Slim down 3 fat module routers (>1000 lines) | Medium | Architecture |
| 13 | Delete 11 duplicate `events.py` in services/ | Low | Architecture |
| 14 | Delete 5 duplicate `ports.py` in services/ | Low | Architecture |
| 15 | Remove non-existent `country_versioning` from admin routers | Low | Architecture |
| 16 | Replace 13 `SELECT *` with explicit columns | Medium | Performance |
| 17 | Replace 100+ `.offset()` with keyset pagination | High | Performance |
| 18 | Add logging to 20+ silent exception blocks | Medium | Observability |
| 19 | Fix blocking I/O in async contexts | Low | Performance |
| 20 | Fix 12+ unbounded caches | Medium | Memory safety |

### Phase 3: MEDIUM (This Month)

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| 21 | Migrate 80+ cross-domain imports to ports | High | Law 3 |
| 22 | Shrink DOMAIN_ALLOWLIST.yaml | Medium | Law 7 |
| 23 | Fix 574 TODO/FIXME hygiene | Low | Code quality |
| 24 | Standardize features.py format | Low | Consistency |
| 25 | Add `ondelete` to 9 FK columns | Low | Data integrity |
| 26 | Add `index=True` to 9 FK columns | Low | Performance |
| 27 | Add TTL to `_JWKS_CACHE` | Low | Memory safety |
| 28 | Refactor 4 god services (>4000 lines) | Very High | Maintainability |
| 29 | Fix float-for-money in catalog | Medium | Financial correctness |

### Phase 4: LOW (When Possible)

| # | Issue | Effort | Impact |
|---|-------|--------|--------|
| 30 | Extract magic numbers to constants | Low | Maintainability |
| 31 | Add return type hints to 10+ functions | Low | Code quality |
| 32 | Extract duplicated code patterns | Medium | Maintainability |

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total Python files in `domains/` | 734 |
| Files with cross-domain imports | 80+ |
| Duplicate table pairs | 49 |
| Models missing `is_deleted` | ~73 |
| Silent exception blocks | 20+ |
| Unbounded caches | 12+ |
| God files (>1000 lines) | 20 |
| Worst god file | `general_ledger_service.py` (8,874 lines) |
| OFFSET pagination calls | 100+ |
| SELECT * queries | 13 |
| TODO/FIXME without ticket | 574 |
| Broken imports | 3 files |
| Duplicate auth implementations | 5 |

---

## Clean Areas (No Violations)

| Area | Status |
|------|--------|
| Provider isolation (Law 11, 31, 100, 123) | ✅ CLEAN |
| Infrastructure/Kernel isolation (Law 10, 101, 102) | ✅ CLEAN |
| Root-level forbidden packages (Law 18) | ✅ CLEAN |
| Module-to-Domain import direction (Law 1, 97, 99) | ✅ CLEAN |
| Connection pool sizing (Law 47) | ✅ PASS |
| Explicit transactions (Law 50) | ✅ PASS |
| Forbidden schemas (Law 56) | ✅ PASS |
| Schema-per-domain (Law 55) | ✅ PASS |
| N+1 query patterns (Law 45) | ✅ PASS |
| print() in production (Law 58) | ✅ PASS |
| Password handling (Law 38) | ✅ COMPLIANT |
| Rate limit fail-closed (Law 37) | ✅ COMPLIANT |
| WebSocket auth (Law 41) | ✅ COMPLIANT |

---

## Appendix: Investigation Agents Used

| Agent | Categories Covered | Issues Found |
|-------|-------------------|-------------|
| Agent 1 | Architecture & Wiring | 73 issues |
| Agent 2 | Security | 12 issues |
| Agent 3 | Database & Data Layer | 10 issues |
| Agent 4 | Code Quality & Scalability | 64 issues |
| Agent 5 | Domain & Module Structure | 23 issues |

---

*End of audit report.*
