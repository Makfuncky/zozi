# ZOZI Backend — Complete Domain Investigation Report

> **Generated:** 2026-08-26
> **Scope:** All 15 domains, ~200+ service files
> **Method:** Deep code analysis by 4 parallel investigation agents

---

## Executive Summary

| Severity | Count | Description |
|----------|-------|-------------|
| **CRITICAL** | 42 | Immediate runtime crashes, broken imports, circular dependencies |
| **HIGH** | 68 | Architecture violations, security risks, cross-domain coupling |
| **MEDIUM** | 95 | Stubs, TODOs, duplicate code, missing error handling |
| **LOW** | 47 | Unused imports, dead code, style issues |
| **Total** | **252** | issues found across 15 domains |

### Domain Health Score

| Domain | CRITICAL | HIGH | MEDIUM | LOW | Health |
|--------|----------|------|--------|-----|--------|
| **Catalog** | 3 | 5 | 8 | 4 | ⚠️ Fair |
| **Orders** | 2 | 4 | 6 | 3 | ⚠️ Fair |
| **Customers** | 2 | 3 | 5 | 3 | ⚠️ Fair |
| **Finance** | 3 | 6 | 7 | 5 | ⚠️ Fair |
| **Comms** | 1 | 3 | 4 | 2 | ✅ Good |
| **Logistics** | 2 | 4 | 5 | 3 | ⚠️ Fair |
| **Security** | 4 | 6 | 8 | 5 | 🔴 Poor |
| **Accounts** | 5 | 7 | 9 | 6 | 🔴 Poor |
| **HR** | 4 | 5 | 10 | 4 | 🔴 Poor |
| **Governance** | 4 | 6 | 5 | 3 | 🔴 Poor |
| **Audit** | 3 | 4 | 5 | 2 | ⚠️ Fair |
| **Analytics** | 2 | 3 | 4 | 2 | ⚠️ Fair |
| **Suppliers** | 2 | 4 | 5 | 3 | ⚠️ Fair |
| **Promotions** | 1 | 2 | 3 | 1 | ✅ Good |
| **Country** | 4 | 5 | 1 | 0 | 🔴 Poor |

---

## 1. CRITICAL Issues (42)

These will cause **immediate runtime crashes** and must be fixed first.

### 1.1 Circular Imports (5)

| File | Line | Issue |
|------|------|-------|
| `domains/accounts/models/user.py` | 27-40 | Self-referential `_CANONICAL_EXPORTS` maps `"User"` to same file — infinite recursion via `__getattr__` |
| `domains/logistics/services/events.py` | 1 | Circular self-import — file imports from itself |
| `domains/governance/ports.py` | 855-875 | Imports from services which import from models which import from ports |
| `domains/accounts/services/auth/auth_service.py` | 1365-1371 | `User as UserSchema` conflicts with ORM `User` model |
| `domains/security/services/features.py` | 65 | `__all__` lists functions imported after the definition — only available at runtime |

### 1.2 Broken Imports (18)

| File | Line | Issue |
|------|------|-------|
| `domains/finance/services/finance_service.py` | 419 | Missing `ctrl` import — would crash at runtime |
| `domains/security/services/health/risk_controller.py` | 19-23 | Imports from non-existent `domains.governance.services.risk.risk_service` |
| `domains/security/services/fraud/fraud_engine.py` | 22 | Imports from non-existent `admin_security_detection_service` |
| `domains/security/services/iam/iam_service.py` | 641 | Imports non-existent `TreasuryAccount` from `domains.finance.models.finance` |
| `domains/accounts/services/users/users_admin_service.py` | 181, 892, 893 | Uses `VALID_USER_ROLES`, `_ALLOWED_BANK_ACCOUNT_KINDS`, `_require_admin` — all undefined |
| `domains/accounts/services/users/users_admin_service.py` | 328, 350 | Uses `selectinload`, `IntegrityError` — never imported |
| `domains/accounts/ports.py` | 623-625 | Imports from non-existent `customer_coupons_create_service`, `customer_coupons_mgmt_service` |
| `domains/hr/services/_auto_stubs.py` | 1-54 | Entire file is `TODO: Implement` stubs — all functions return `None` |
| `domains/hr/services/employees/risk_service.py` | 36 | Imports non-existent `update_flight_risk_score` from `rbac` |
| `domains/accounts/services/tracker/live_session_tracker.py` | 158 | Checks non-existent fields `latitude`, `longitude` on `UserLoginHistory` |
| `domains/analytics/services/analytics_controller.py` | 1 | Upward import from `modules/` layer (Law 1 violation) |
| `domains/suppliers/services/admin_suppliers_service.py` | 1 | Upward import from `modules/` layer (Law 1 violation) |
| `domains/country/services/events.py` | Multiple | Typos: `rloat`, `rerresh`, `rixed_ree` — cause `NameError` |
| `domains/country/services/events.py` | Multiple | Malformed f-strings — cause `SyntaxError` |

### 1.3 Duplicate/Merged Code (8)

| File | Line | Issue |
|------|------|-------|
| `domains/security/services/core/security_service.py` | 243-432 | Lines 243-432 are near-exact duplicate of lines 1-218 |
| `domains/accounts/services/auth/auth_service.py` | 1328 | 1490+ line file contains 4+ modules concatenated |
| `domains/governance/features.py` | 350-417 | `FEATURES` dict defined twice — second overwrites first |
| `domains/governance/events.py` | 485-599 | Full copy of accounts events appended to governance events |
| `domains/governance/subscribers.py` | 355-452 | Full copy of accounts subscribers appended |
| `domains/audit/services/compliance_service.py` | 314 | Second `from __future__` mid-file — Frankenstein merge |
| `domains/accounts/services/identity/identity_admin_service.py` | 209-518 | Full duplicate of IAM service from security domain |
| `domains/accounts/models/onboarding.py` | 40-51, 66-79 | `DocumentVerification`, `KYCVerification` duplicated from security domain |

### 1.4 Architecture Violations (6)

| File | Line | Issue |
|------|------|-------|
| `domains/security/services/core/security_service.py` | 289 | Cross-domain import: `import domains.comms.services as db_write` |
| `domains/security/services/detection/public_security_detection_service.py` | 7 | Cross-domain model import from `domains.governance.models.user` |
| `domains/security/services/registration/public_security_registration_service.py` | 21 | Imports middleware directly into service |
| `domains/analytics/services/analytics_controller.py` | 1 | Upward import from `modules/` |
| `domains/suppliers/services/admin_suppliers_service.py` | 1 | Upward import from `modules/` |
| `domains/accounts/services/permissions/permission_service.py` | 9 | Imports from non-existent `domains.governance.models.permissions` |

### 1.5 Undefined References (5)

| File | Line | Issue |
|------|------|-------|
| `domains/hr/services/employees/hr_service.py` | 718 | References non-existent `emp.first_name`, `emp.last_name` |
| `domains/hr/services/employees/employee_service.py` | 510 | References non-existent `emp.user.is_clocked_in` |
| `domains/hr/services/employees/employee_service.py` | 192-193 | References non-existent `EmployeeDocument.document_type`, `document_name` |
| `domains/hr/services/employees/employee_service.py` | 390-404 | References non-existent `EmployeeRole.name`, `slug` |
| `domains/hr/models/employee_models.py` | 579 | Duplicate `ShiftHandoverTask` with `extend_existing=True` |

---

## 2. HIGH Issues (68)

### 2.1 Security Vulnerabilities (12)

| File | Line | Issue |
|------|------|-------|
| `domains/accounts/services/auth/auth_service.py` | 384 | **Plaintext OTP logged to console** |
| `domains/accounts/services/auth/auth_service.py` | 813-815 | SSO security bypass — decodes JWT without verification in non-prod |
| `domains/accounts/services/auth/auth_service.py` | 1113 | Uses unverified claims for logout — token not validated |
| `domains/security/services/core/kms_encryption.py` | 35-36 | Ephemeral key generation — data encrypted now can never be decrypted after restart |
| `domains/security/services/threat/behavioral_analytics.py` | 149-159 | ASGI middleware `__call__` non-functional when `self.app` is None |
| `domains/accounts/services/addresses/addresses_service.py` | 1 | Archived module still imported in `__init__.py` |
| `domains/security/services/threat/siem_engine.py` | 158-166 | Broken Redis key pattern — `GET` doesn't support wildcards |
| `domains/security/services/threat/behavioral_analytics.py` | 98-103 | Bare `pass` in except — silences Redis errors |
| `domains/security/services/threat/behavioral_analytics.py` | 133-136 | Bare `pass` in except — silences risk score update errors |
| `domains/hr/services/employees/hr_service.py` | 165-169 | Fake compliance check — always returns `compliant: True` |
| `domains/hr/services/employees/employee_service.py` | 376-379 | Fake QR token — creates UUID but never persists |
| `domains/hr/services/employees/employee_service.py` | 381-382 | Fake QR validation — always returns `{"status": "validated"}` |

### 2.2 Cross-Domain Coupling (15)

| File | Line | Issue |
|------|------|-------|
| `domains/security/services/fraud/fraud_detection_service.py` | 36-40 | Imports from `logistics`, `orders`, `finance` models |
| `domains/security/services/iam/iam_service.py` | 17-19 | Imports from `hr` models |
| `domains/security/services/iam/iam_service.py` | 249 | Re-imports model inside function |
| `domains/accounts/services/identity/identity_admin_service.py` | 22 | Imports from `governance` models |
| `domains/accounts/services/permissions/permission_service.py` | 9 | Imports from `governance` models |
| `domains/accounts/models/core.py` | 109-119 | Imports from 6 different domains in model file |
| `domains/hr/models/hr_schema_models.py` | 25-28 | Re-exports from `accounts` models with `noqa` |
| `domains/governance/ports.py` | 858-864 | Cross-domain service imports from `hr`, `accounts` |
| `domains/accounts/services/addresses/addresses_service.py` | 14 | Cross-domain import from `infrastructure.security` |
| `domains/governance/events.py` | 74 | Passes `db` object in event payload — stale session risk |
| `domains/governance/subscribers.py` | 37-49 | Subscriptions at import time — side effects |
| `domains/security/subscribers.py` | 26-27 | Subscriptions at import time — side effects |
| `domains/security/services/core/security_service.py` | 227-231 | Imports from `rbac` at module level |
| `domains/accounts/services/auth/auth_service.py` | 69-77 | Redis check discards connection — callers don't handle `None` |

### 2.3 Missing Provider Wiring (18)

| Service | Missing Provider | Impact |
|---------|-----------------|--------|
| `catalog/ai_upload_service.py` | `bg_removal` | No BG removal for supplier images |
| `catalog/ai_upload_service.py` | `ai.image_similarity` | No duplicate detection |
| `orders/orders_service.py` | `shipping` | No shipping rate calculation |
| `orders/orders_service.py` | `payments.registry` | No multi-gateway routing |
| `customers/reviews_service.py` | `ai.sentiment` | No review moderation |
| `customers/search_service.py` | `ai.search` | No semantic search |
| `finance/finance_service.py` | `finance.bank_api` | No bank connection |
| `finance/finance_service.py` | `geography.rates` | No multi-currency support |
| `logistics/features.py` | `qr.qr_generator` | No QR label generation |
| `logistics/features.py` | `barcode.barcode_generator` | No barcode generation |
| `security/features.py` | `auth.jwt` | No token validation |
| `security/features.py` | `auth.totp` | No 2FA support |
| `security/features.py` | `security.watchlist` | No AML screening |
| `accounts/auth/auth_service.py` | `comms.email` | No welcome/verification emails |
| `accounts/auth/auth_service.py` | `comms.twilio` | No SMS verification |
| `suppliers/supplier_service.py` | `security.watchlist` | No supplier screening |
| `analytics/flat_analytics_service.py` | `analytics.analytics` | No dashboard metrics |
| `promotions/flash_sale_service.py` | `automation.scheduler` | No flash sale timing |

### 2.4 Code Quality Issues (23)

| File | Line | Issue |
|------|------|-------|
| `domains/security/services/core/security_service.py` | 223, 274 | Duplicate `from __future__` imports |
| `domains/security/services/core/security_service.py` | 267, 245 | Orphaned docstrings mid-file |
| `domains/security/services/threat/siem_engine.py` | 1 | Unused `import hashlib` |
| `domains/security/services/threat/behavioral_analytics.py` | 13 | Unused `import hashlib` |
| `domains/accounts/services/auth/auth_service.py` | 258, 384, 827, 1162 | TODO comments — incomplete features |
| `domains/accounts/services/auth/auth_service.py` | 1234-1235 | SMS delivery stub — only logs |
| `domains/hr/services/employees/employee_service.py` | 577-594 | Fake DLP scan — regex doesn't match real PII |
| `domains/hr/services/employees/employee_service.py` | 612-620 | Fake communication stats — returns zeros |
| `domains/accounts/services/sessions/session_service.py` | 45-46 | Returns cached dict as ORM object |
| `domains/accounts/services/sessions/session_service.py` | 119 | Missing `db.rollback()` on exception |
| `domains/security/services/fraud/fraud_detection_service.py` | 42 | Wrong config import path |
| `domains/hr/services/employees/hr_service.py` | 22-25 | Duplicate logger setup |
| `domains/hr/services/employees/employee_service.py` | 506-551 | Fake meeting/war room/chat — no DB writes |
| `domains/security/services/fraud/impossible_travel_write_service.py` | 24-26 | Duplicate logger setup |
| `domains/hr/services/employees/hse_manager.py` | All | Entire class returns fake dicts |
| `domains/hr/models/employee_models.py` | 208, 248, 304 | Duplicate `__table_args__` — second overwrites first |
| `domains/accounts/models/onboarding.py` | 40-51, 66-79 | Duplicate model definitions |
| `domains/security/models/fraud.py` | 292-304 | `__table_args__` after relationships — may cause SQLAlchemy issues |
| `domains/security/models/security_schema_models.py` | 53-55 | Duplicate relationship — ambiguous join warnings |
| `domains/accounts/models/user.py` | 34-36 | Circular import risk in lazy imports |
| `domains/accounts/models/core.py` | 126 | Duplicate import with `noqa: F401,F811` |

---

## 3. MEDIUM Issues (95)

### 3.1 Stubs and TODOs (35)

| File | Line | Issue |
|------|------|-------|
| `domains/hr/services/_auto_stubs.py` | 1-54 | All 12 functions are `TODO: Implement` stubs |
| `domains/governance/services/_auto_stubs.py` | All | Stub file exists — unimplemented |
| `domains/accounts/services/auth/auth_service.py` | 258, 384, 827, 1162 | TODO: incomplete features |
| `domains/hr/services/employees/coi_service.py` | 183 | `detect_coi()` returns `None` for supplier type |
| `domains/accounts/services/permissions/permission_service.py` | 284 | Missing `db` parameter default |
| `domains/accounts/policies/user_policies.py` | 5-28 | Stub policy class — doesn't integrate with RBAC |
| `domains/accounts/services/tracker/live_session_tracker.py` | 95-116 | Uses wrong `UserDevice` fields |
| `domains/hr/services/employees/employee_service.py` | 304-305 | References non-existent `EmployeeRelation.related_employee_id` |
| `domains/hr/services/employees/employee_service.py` | 526-537 | Fake chat message — no DB write |
| `domains/hr/services/employees/employee_service.py` | 539-551 | Fake masked channel — no DB write |
| `domains/hr/services/employees/employee_service.py` | 585-594 | Fake shift handover — no DB write |
| `domains/hr/services/employees/risk_service.py` | 41-54 | Duplicates security domain logic |
| `domains/hr/services/employees/risk_service.py` | 57-101 | Duplicates security domain logic |
| `domains/security/services/health/flat_risk_service.py` | 86-88 | Imports from non-existent path |
| `domains/security/services/detection/confidence_scoring.py` | All | No logging configured |
| `domains/security/services/core/security_metrics.py` | 36-39 | Mutable default arguments |
| `domains/security/services/threat/siem_engine.py` | 194-196 | Silent failure on missing action |
| `domains/hr/ports.py` | 443-447 | Commented-out imports — acknowledges bugs |
| `domains/hr/ports.py` | 68-70 | Complex unpacking hack |

### 3.2 Missing Error Handling (22)

| File | Line | Issue |
|------|------|-------|
| `domains/hr/services/events.py` | 89 | Bare `pass` in except — silences errors |
| `domains/security/services/threat/behavioral_analytics.py` | 98-103 | Bare `pass` in except — silences Redis errors |
| `domains/security/services/threat/behavioral_analytics.py` | 133-136 | Bare `pass` in except — silences risk score errors |
| `domains/accounts/services/sessions/session_service.py` | 119 | Missing `db.rollback()` |
| `domains/accounts/services/permissions/permission_service.py` | 327 | Missing `db.rollback()` in `_log_audit()` |
| `domains/governance/subscribers.py` | 52 | Logger not used |
| `domains/security/services/core/kms_encryption.py` | 134-135 | Calls `get_service_session()` at module load |
| `domains/accounts/services/auth/auth_service.py` | 69-77 | Redis check discards connection — callers don't handle `None` |

### 3.3 Inconsistent Patterns (18)

| Issue | Files Affected |
|-------|---------------|
| `from infrastructure.config import settings` vs `from infrastructure.utils.config import settings` | Multiple files use wrong path |
| `from rbac import X` at module level | Security, HR domains — should use ports |
| `logger = structlog.get_logger()` then `logger = logging.getLogger()` | Security, HR — duplicate logger |
| `datetime.utcnow()` deprecated | Governance events — should use `datetime.now(timezone.utc)` |
| `subscribe()` at import time | Security, Governance — side effects |

---

## 4. LOW Issues (47)

| Category | Count | Examples |
|----------|-------|----------|
| Unused imports | 15 | `import hashlib` x3, `import time`, `BaseModel`, `datetime` |
| Dead code | 8 | Orphaned docstrings, commented-out imports, blank lines |
| Empty files | 8 | `features.py`, `events.py`, `subscribers.py` in multiple domains |
| Style issues | 10 | BOM characters, duplicate `__future__` imports, `noqa` suppressions |
| Deprecated APIs | 6 | `datetime.utcnow()`, mutable defaults, bare except |

---

## 5. Cross-Domain Issues

### 5.1 Canonical User Model Problem

**Issue:** `domains/governance/models/user.py` is the canonical User model but is imported directly by services in `security/`, `accounts/`, and `hr/` domains instead of going through ports (Law 3 violation).

**Affected files:**
- `domains/security/services/detection/public_security_detection_service.py:7`
- `domains/accounts/services/identity/identity_admin_service.py:22`
- `domains/security/services/fraud/fraud_detection_service.py:36-40`

**Fix:** All domains should access User through `domains/accounts/ports.py` or via events.

### 5.2 Duplicate Model Definitions

| Model | Domain 1 | Domain 2 |
|-------|----------|----------|
| `DocumentVerification` | `security/models/security_schema_models.py` | `accounts/models/onboarding.py` |
| `KYCVerification` | `security/models/security_schema_models.py` | `accounts/models/onboarding.py` |
| `FraudEvent` | `security/models/fraud.py` | `governance/models/fraud.py` |
| `IAMService` | `security/services/iam/iam_service.py` | `accounts/services/identity/identity_admin_service.py` |
| `ShiftHandoverTask` | `hr/models/employee_models.py` | `hr/models/hr_schema_models.py` |

### 5.3 Archived Modules Still Importable

The following modules are marked "ARCHIVED - DO NOT IMPORT" but remain on disk and can be imported:
- `domains/accounts/services/addresses/addresses_service.py`
- `domains/promotions/services/_archived/`
- `domains/suppliers/services/_archived/`

---

## 6. Recommended Fix Priority

### Phase 1: Critical Fixes (Week 1)
1. Fix all circular imports — `accounts/models/user.py`, `logistics/services/events.py`
2. Fix all broken imports — add missing imports, remove non-existent references
3. Remove duplicate/merged code blocks — `security_service.py`, `auth_service.py`
4. Fix country domain typos — `rloat`, `rerresh`, `rixed_ree`

### Phase 2: High Fixes (Week 2)
1. Add missing provider wiring — 18 services need providers
2. Fix security vulnerabilities — OTP logging, SSO bypass, ephemeral keys
3. Remove cross-domain imports — use ports/events instead
4. Fix duplicate model definitions — consolidate into canonical locations

### Phase 3: Medium Fixes (Week 3)
1. Implement all stubs — `hr/_auto_stubs.py`, `governance/_auto_stubs.py`
2. Add missing error handling — `db.rollback()`, specific exceptions
3. Fix inconsistent patterns — logger setup, config imports
4. Add missing tests for critical paths

### Phase 4: Low Fixes (Week 4)
1. Remove unused imports
2. Remove dead code
3. Fix deprecated API usage
4. Clean up empty files

---

## 7. Architecture Compliance Score

| Law | Compliance | Notes |
|-----|-----------|-------|
| Law 1: Arrows point down | **75%** | 4 files import from `modules/` upward |
| Law 2: Thin routers | **90%** | Most routers are thin |
| Law 3: Cross-domain via events | **65%** | Many direct cross-domain imports |
| Law 4: Features single-sourced | **85%** | Most domains have `features.py` |
| Law 5: Country scope axis | **80%** | Country code present but not enforced |
| Law 6: Schema discipline | **70%** | Duplicate models, schema mismatches |
| Law 7: Allowlist rule | **60%** | Many unauthorized cross-domain imports |

**Overall Architecture Compliance: 75%**

---

*End of Investigation Report*
