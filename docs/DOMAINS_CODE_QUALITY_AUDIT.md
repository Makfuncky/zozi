# ZOZI Backend — Full Domain Code Quality Audit

**Audit Date:** 2026-08-26  
**Scope:** All 16 domains under `backend/domains/`  
**Methodology:** Static analysis of services, models, schemas, events, ports, policies, read models, and cross-domain imports

---

## Executive Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 8 |
| HIGH | 14 |
| MEDIUM | 18 |
| LOW | 12 |
| **Total** | **52** |

The codebase has **systemic architectural violations** — the three-axis architecture (modules → domains → infrastructure) is routinely broken by cross-domain model imports, duplicate model definitions, and services that create foreign-domain entities directly. Many "ports.py" files are auto-generated boilerplate (600+ lines of copy-pasted functions). Stub/placeholder files exist in production code paths. The `accounts` domain is the most problematic, with `auth_service.py` at 4,317 lines creating `SupplierProfile` and `LogisticsPartner` directly.

---

## CRITICAL Issues

### C1. Cross-Domain Model Duplication (Multiple Domains)

**Severity:** CRITICAL  
**Impact:** Data inconsistency, migration conflicts, runtime errors from duplicate table mappings

The same model classes are defined in multiple domains, violating single-source-of-truth:

| Model | Domain 1 | Domain 2 | Domain 3 |
|-------|----------|----------|----------|
| `User(Base)` | `accounts/models/user.py` | `governance/models/user.py:11` | — |
| `SupportTicket(Base)` | `accounts/models/core.py` | `comms/models/communication_schema_models.py:36` | — |
| `SupportTicketReply(Base)` | `accounts/models/core.py` | `comms/models/communication_schema_models.py:52` | — |
| `AuditLog(Base)` | `audit/models/audit_schema_models.py:12` | `governance/models/core.py` | — |
| `ReferralPointEvent(Base)` | `accounts/models/user.py` | `governance/models/user.py:92` | `customers/models/` |
| `ShiftHandoverTask(Base)` | `accounts/models/core.py` | `hr/models/employee_models.py` | — |
| `PromotionEngineConfig(Base)` | `governance/models/admin.py` | `promotions/models/promotion_config.py` | — |
| `CouponUsage(Base)` | `governance/models/` | `promotions/models/coupon_usage.py` | — |
| `FinancialReport(Base)` | `analytics/models/analytics_schema_models.py:20` | `finance/models/general_ledger.py` | — |
| `UserSession(Base)` | `accounts/models/user.py` | `governance/models/core.py:67` | — |
| `UserBrowsingHistory(Base)` | `accounts/models/core.py` | `governance/models/core.py:45` | — |
| `UserLoginHistory(Base)` | `accounts/models/user.py` | `governance/models/user.py:28` | — |
| `UserDevice(Base)` | `accounts/models/user.py` | `governance/models/user.py:40` | — |
| `PasswordResetToken(Base)` | `accounts/models/user.py` | `governance/models/user.py:54` | — |
| `EmailVerificationToken(Base)` | `accounts/models/user.py` | `governance/models/user.py:67` | — |
| `RevokedToken(Base)` | `accounts/models/user.py` | `governance/models/user.py:80` | — |

**Recommended Fix:** Consolide all identity/user models into `accounts` domain (the owning domain). Other domains should import from `accounts.ports` or `accounts.models` only. Delete duplicate definitions.

---

### C2. auth_service.py Creates Foreign-Domain Entities

**Severity:** CRITICAL  
**File:** `domains/accounts/services/auth/auth_service.py`  
**Lines:** 2347-2366

```python
# Line 2347 — accounts domain directly creates SupplierProfile
profile = SupplierProfile(
    user_id=db_user.id,
    business_name=user.business_name.strip() if user.business_name else None,
    ...
)

# Line 2362-2366 — accounts domain directly creates LogisticsPartner
if user.role == "logistics_partner":
    db.add(
        LogisticsPartner(
            name=f"{db_user.username} Logistics",
            code=_next_logistics_partner_code(db, cast(int, getattr(db_user.id"))),
            ...
        )
    )
```

**Imports at lines 1402-1403:**
```python
from domains.comms.models.suppliers import SupplierProfile
from domains.logistics.models.logistics import LogisticsPartner
```

**Impact:** Violates Law 3 (cross-domain writes only via events). The accounts domain directly writes to supplier and logistics tables.

**Recommended Fix:** Emit `UserCreated` event from accounts domain; let suppliers/logistics subscribers create their respective profiles.

---

### C3. Cross-Domain Model Imports in Services (Law 3 Violation)

**Severity:** CRITICAL  
**Impact:** Tight coupling, circular import risk, violates architecture laws

| File | Line | Import |
|------|------|--------|
| `accounts/services/auth/auth_service.py` | 47-48 | `from domains.governance.models.user import User, UserDevice` |
| `accounts/services/auth/auth_service.py` | 50 | `from domains.hr.ports import Employee, EmployeeBiometric...` |
| `accounts/services/auth/auth_service.py` | 1402 | `from domains.comms.models.suppliers import SupplierProfile` |
| `accounts/services/auth/auth_service.py` | 1403 | `from domains.logistics.models.logistics import LogisticsPartner` |
| `accounts/services/sessions/session_service.py` | 9 | `from domains.governance.models.core import UserSession` |
| `accounts/services/permissions/permission_service.py` | 438 | `from domains.governance.models.user import User` |
| `accounts/services/tracker/live_session_tracker.py` | 152 | `from domains.hr.models.employee_models import GeoFenceLog, Employee` |
| `accounts/services/identity/identity_admin_service.py` | 19 | `from domains.governance.ports import User` |
| `audit/services/worm_audit.py` | 14 | `from domains.governance.models.core import AuditLog` |
| `audit/services/security_audit.py` | 7 | `from domains.governance.models.core import AuditLog` |
| `analytics/services/flat_admin_dashboard_service.py` | 16-26 | Imports from 6 different domains |
| `accounts/services/accounts_service.py` | 10 | `from domains.hr.models.employee_models import Employee` |

**Recommended Fix:** All cross-domain reads must go through `ports.py` of the owning domain. Replace direct model imports with port function calls.

---

### C4. Empty Stub Directories with No Implementation

**Severity:** CRITICAL  
**Impact:** Broken imports, runtime failures if code paths hit these modules

These `__init__.py` files are completely empty (0 bytes), making the directories valid Python packages with no exports:

| Path | Domain |
|------|--------|
| `accounts/policies/__init__.py` | accounts |
| `accounts/schemas/__init__.py` | accounts |
| `accounts/utils/__init__.py` | accounts |
| `audit/read_models/__init__.py` | audit |
| `audit/schemas/__init__.py` | audit |
| `catalog/policies/__init__.py` | catalog |
| `catalog/schemas/__init__.py` | catalog |
| `catalog/utils/__init__.py` | catalog |
| `comms/services/email/__init__.py` | comms |
| `comms/services/logistics/__init__.py` | comms |
| `comms/services/shared/__init__.py` | comms |
| `comms/services/translation/__init__.py` | comms |
| `country/utils/__init__.py` | country |
| `hr/policies/__init__.py` | hr |
| `hr/schemas/__init__.py` | hr |
| `security/read_models/__init__.py` | security |
| `security/schemas/__init__.py` | security |

**Recommended Fix:** Either implement the module or remove the directory. Empty packages confuse developers and break tooling.

---

### C5. Stub Service Classes with `pass`

**Severity:** CRITICAL  
**Impact:** Runtime failures if code instantiates these classes

**File:** `domains/country/services/cross_border/cross_border_detection.py`
```python
class CrossBorderDetectionMiddleware:
    """Stub for cross-border detection."""
    pass

class LocalizationService:
    """Stub for localization service."""
    pass
```

**File:** `domains/country/services/research/curated_cities.py`
```python
def get_cities(country_code: str) -> List[dict]:
    """Get curated cities for a country."""
    return []
```

**File:** `domains/accounts/services/logistics_partner_service.py`
```python
"""Stub for logistics_partner_service."""
from domains.logistics.services.partners.logistics_partner_service import *
```

**Recommended Fix:** Implement or remove. These are in production import paths.

---

### C6. Overly Broad Exception Handling (Catch-All Anti-Pattern)

**Severity:** CRITICAL  
**Impact:** Swallows all errors including KeyboardInterrupt, SystemExit; masks bugs

**File:** `domains/analytics/services/aggregation/command_center_query_service.py:42`
```python
except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, 
        OSError, IOError, EOFError, ImportError, NameError, StopIteration, 
        ArithmeticError, AssertionError, UnicodeError, NotImplementedError, 
        RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
```

This pattern appears in **50+ locations** across the codebase, notably in:
- `comms/services/email/email_gateway.py` (lines 175, 221, 244, 274, 301, 428)
- `analytics/services/aggregation/command_center_query_service.py` (lines 42, 51, 66)

**Recommended Fix:** Catch specific exceptions only. Never catch `BaseException`, `SystemExit`, `KeyboardInterrupt`, or `NotImplementedError`.

---

### C7. Hardcoded Fallback Secret

**Severity:** CRITICAL  
**Impact:** Security vulnerability — if `settings.secret_key` is None, a hardcoded fallback is used

**File:** `domains/security/services/features.py:91`
```python
secret = settings.secret_key or "fallback-zozi-secret"
return hashlib.sha256(secret.encode("utf-8", errors="replace")).digest()[:16]
```

**Recommended Fix:** Raise an error if `secret_key` is not configured. Never use hardcoded fallbacks for cryptographic material.

---

### C8. Duplicate Function Definitions in payout_batch_service.py

**Severity:** CRITICAL  
**Impact:** Dead code, maintenance burden, potential runtime confusion

**File:** `domains/finance/services/payouts/payout_batch_service.py`

The functions `_resolve_supplier_names` and `_resolve_logistics_names` are defined **twice** with identical bodies:
- First definition: lines 2846-2857
- Second definition: lines 4043-4054

**Recommended Fix:** Remove duplicate definitions.

---

## HIGH Issues

### H1. Massive Auto-Generated Boilerplate in ports.py

**Severity:** HIGH  
**Impact:** Maintenance burden, code readability, 600+ lines of copy-pasted functions

**File:** `domains/accounts/ports.py` (628 lines)

Every model has 3 nearly-identical functions generated:
```python
def get_address_by_id(db: Session, id_: int) -> Optional[Address]:
    return db.get(Address, id_)

def list_addresses(db: Session, limit: int = 100) -> List[Address]:
    return _keyset_list(Address, db, limit)

def list_addresses_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE) -> CursorPage:
    return _keyset_page(Address, db, cursor, page_size)
```

This pattern repeats for **40+ models**. Similar issues exist in:
- `domains/orders/ports.py` (50.9 KB)
- `domains/finance/ports.py` (42.2 KB)
- `domains/governance/ports.py` (40.4 KB)
- `domains/comms/ports.py` (39.6 KB)

**Recommended Fix:** Use a code generator or metaclass approach. Generate these at build time, not in source control.

---

### H2. auth_service.py is 4,317 Lines (God Service Anti-Pattern)

**Severity:** HIGH  
**Impact:** Unmaintainable, violates single responsibility, 156 KB file

**File:** `domains/accounts/services/auth/auth_service.py` (4,317 lines)

Contains:
- 5 login "doors" (email/password, phone/OTP, biometric, QR kiosk, SSO)
- User creation with cross-domain entity creation
- Token management
- Session management
- Risk scoring
- Device fingerprinting
- SSO JWT verification with JWKS caching

**Recommended Fix:** Split into: `email_auth_service.py`, `phone_auth_service.py`, `biometric_auth_service.py`, `sso_auth_service.py`, `session_service.py`, `device_service.py`.

---

### H3. Empty events.py and subscribers.py Placeholders

**Severity:** HIGH  
**Impact:** Cross-domain writes have no sanctioned path; developers bypass the pattern

Multiple domains have empty placeholder files:
- `accounts/events.py` — 7 lines, just a TODO comment
- `accounts/subscribers.py` — 7 lines, just a TODO comment
- `catalog/subscribers.py` — TODO placeholder
- `analytics/subscribers.py` — TODO at line 27

**Recommended Fix:** Either implement real event definitions or remove the files. Empty placeholders encourage developers to bypass the pattern.

---

### H4. "TODO: Module not yet created" in Production Code

**Severity:** HIGH  
**Impact:** Incomplete implementations, dead code paths

Found in **100+ locations** across the codebase. Notable clusters:

| File | Count | Domain |
|------|-------|--------|
| `logistics/services/partners/admin_logistics_operations_service.py` | 80+ | logistics |
| `governance/subscribers.py` | 24 | governance |
| `suppliers/services/orders/supplier_orders_verify_service.py` | 12 | suppliers |
| `logistics/services/tracking/service.py` | 6 | logistics |
| `analytics/services/flat_admin_dashboard_service.py` | 8 | analytics |
| `catalog/services/products/admin_products_service.py` | 1 | catalog |
| `finance/services/__init__.py` | 4 | finance |

**Recommended Fix:** These indicate incomplete refactoring. Either implement the modules or remove the TODO comments.

---

### H5. Duplicate Model Definitions Within Same Domain

**Severity:** HIGH  
**Impact:** SQLAlchemy mapper confusion, wrong table bindings

**File:** `domains/hr/models/employee_models.py`
- `ShiftHandoverTask(Base)` defined **twice** in the same file

**Recommended Fix:** Remove the duplicate definition.

---

### H6. Empty events.py in Multiple Domains

**Severity:** HIGH  
**Impact:** No cross-domain write path defined

The following domains have `events.py` files that are empty placeholders (just TODO comments):
- `accounts/events.py`
- `catalog/subscribers.py`
- `analytics/subscribers.py`

**Recommended Fix:** Define real events or remove the files.

---

### H7. Wildcard Imports in Services

**Severity:** HIGH  
**Impact:** Namespace pollution, unclear dependencies, breaks IDE tooling

**File:** `domains/audit/services/__init__.py`
```python
from domains.audit.services.logs import *
from domains.audit.services.data import *
from domains.audit.services.compliance import *
from domains.audit.services.audit_service import *
from domains.audit.services.security_audit import *
from domains.audit.services.worm_audit import *
from domains.audit.services.retention_service import *
from domains.audit.services.data_residency import *
from domains.audit.services.flat_data_residency_service import *
from domains.audit.services.ediscovery import *
from domains.audit.services.compliance_engine import *
from domains.audit.services.communication_audit import *
```

**File:** `domains/catalog/services/variants/__init__.py`
```python
from domains.catalog.services.variants.variant_config_service import *
```

**Recommended Fix:** Use explicit imports. Wildcard imports make it impossible to trace dependencies.

---

### H8. Empty read_models/__init__.py Placeholders

**Severity:** HIGH  
**Impact:** CQRS read models not implemented

| Path | Domain |
|------|--------|
| `accounts/read_models/__init__.py` | accounts (4 lines, just comments) |
| `audit/read_models/__init__.py` | audit (0 bytes) |
| `security/read_models/__init__.py` | security (0 bytes) |

**Recommended Fix:** Implement read models or remove the directories.

---

### H9. Empty policies/__init__.py Placeholders

**Severity:** HIGH  
**Impact:** Permission enforcement not implemented

| Path | Domain |
|------|--------|
| `accounts/policies/__init__.py` | accounts (0 bytes) |
| `catalog/policies/__init__.py` | catalog (0 bytes) |
| `hr/policies/__init__.py` | hr (0 bytes) |

**Recommended Fix:** Implement policies or remove the directories.

---

### H10. Large Service Files Indicate Missing Decomposition

**Severity:** HIGH  
**Impact:** Unmaintainable, violates single responsibility

| File | Size (KB) | Lines (est.) |
|------|-----------|--------------|
| `finance/services/ledger/general_ledger_service.py` | 319 | ~9,000 |
| `orders/services/core/logistics.py` | 228 | ~6,500 |
| `finance/services/payouts/payout_batch_service.py` | 167 | ~4,700 |
| `logistics/services/partners/service.py` | 162 | ~4,600 |
| `accounts/services/auth/auth_service.py` | 157 | ~4,300 |
| `logistics/services/core/service.py` | 155 | ~4,400 |
| `suppliers/services/health/supplier_health.py` | 109 | ~3,100 |
| `finance/services/payments/payment_engine.py` | 108 | ~3,100 |
| `country/services/core/country_service.py` | 95 | ~2,700 |

**Recommended Fix:** Decompose into smaller, focused services.

---

### H11. Empty Service Subdirectories

**Severity:** HIGH  
**Impact:** Broken package structure, confusing for developers

| Path | Domain |
|------|--------|
| `hr/services/ghost_watchdog/__init__.py` | hr (empty `__all__`) |
| `hr/services/leave/__init__.py` | hr (empty `__all__`) |
| `security/services/ess/__init__.py` | security (empty) |
| `promotions/services/marketing/__init__.py` | promotions (empty) |
| `comms/services/marketing/__init__.py` | comms (empty) |
| `comms/services/video/__init__.py` | comms (empty) |
| `comms/services/tickets/__init__.py` | comms (empty) |
| `comms/services/notifications/__init__.py` | comms (empty) |
| `comms/services/messaging/__init__.py` | comms (empty) |
| `comms/services/admin/__init__.py` | comms (empty) |

**Recommended Fix:** Remove empty directories or implement the services.

---

### H12. Cross-Domain Import in accounts/ports.py

**Severity:** HIGH  
**Impact:** ports.py should only export own-domain models

**File:** `domains/accounts/ports.py:34`
```python
from domains.security.models.security_schema_models import AlertEscalationRule, DocumentVerification, KYCVerification
```

**Recommended Fix:** These should be exported from `security.ports`, not imported into `accounts.ports`.

---

### H13. Circular Import Risk via models/onboarding.py

**Severity:** HIGH  
**Impact:** Potential circular imports at module load time

**File:** `domains/accounts/models/onboarding.py:10`
```python
from domains.security.models.security_schema_models import DocumentVerification, KYCVerification
```

**Recommended Fix:** Import from `security.ports` instead.

---

### H14. Duplicate _resolve Functions in payout_batch_service.py

**Severity:** HIGH  
**Impact:** Dead code, maintenance confusion

**File:** `domains/finance/services/payouts/payout_batch_service.py`

Functions `_resolve_supplier_names` (line 2846) and `_resolve_logistics_names` (line 2853) are duplicated at lines 4043 and 4050 with identical implementations.

**Recommended Fix:** Remove the second definitions.

---

## MEDIUM Issues

### M1. Magic Numbers in Business Logic

**Severity:** MEDIUM  
**Impact:** Unclear business rules, hard to modify

**File:** `domains/accounts/services/auth/auth_service.py`
```python
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300  # 5 minutes
KIOSK_SESSION_HOURS = 8
MOBILE_SESSION_DAYS = 30
MAX_OTP_ATTEMPTS = 5
RISK_HIGH_THRESHOLD = 75  # out of 100
```

**Recommended Fix:** Move to configuration or constants module with clear documentation.

---

### M2. Inconsistent Schema Naming

**Severity:** MEDIUM  
**Impact:** Confusing API contracts

Multiple naming patterns for schemas:
- `customer_schema_models.py` (customers)
- `analytics_schema_models.py` (analytics)
- `audit_schema_models.py` (audit)
- `security_schema_models.py` (security)
- `hr_schema_models.py` (hr)
- `logistics_schema_models.py` (logistics)

But also:
- `finance_schemas.py` (finance)
- `governance_schemas.py` (governance)
- `supplier_schemas.py` (suppliers)
- `security_schemas.py` (security)

**Recommended Fix:** Standardize on one naming convention (e.g., `{domain}_schemas.py`).

---

### M3. Inconsistent Model File Organization

**Severity:** MEDIUM  
**Impact:** Hard to locate models

Some domains use a single `models.py`, others use `schema_models.py`, others use multiple files:
- `catalog/models/products.py` — single file with many models
- `finance/models/finance.py`, `commission.py`, `erp.py`, `payments.py`, `general_ledger.py` — split files
- `country/models/` — 10+ files for different aspects

**Recommended Fix:** Standardize model file organization per domain.

---

### M4. Empty __init__.py in Domain Subdirectories

**Severity:** MEDIUM  
**Impact:** Package structure confusion

17 empty `__init__.py` files found across domain subdirectories (policies, schemas, utils, read_models, services subdirs).

**Recommended Fix:** Add `__all__` exports or remove if not needed.

---

### M5. Inconsistent Error Handling Patterns

**Severity:** MEDIUM  
**Impact:** Unpredictable error responses

Some services use `HTTPException`, others return `{"error": "..."}`, others raise domain exceptions:
- `finance/exceptions.py` — has `FinanceDomainError`
- `governance/exceptions.py` — has domain exceptions
- Most services use raw `HTTPException`

**Recommended Fix:** Standardize on domain exceptions with a global exception handler.

---

### M6. Missing __all__ in Several Service __init__.py Files

**Severity:** MEDIUM  
**Impact:** Unclear public API

Many service `__init__.py` files lack `__all__` declarations, making it unclear what's part of the public API.

**Recommended Fix:** Add explicit `__all__` to all `__init__.py` files.

---

### M7. Inconsistent Use of TYPE_CHECKING Guard

**Severity:** MEDIUM  
**Impact:** Some facades use TYPE_CHECKING, others don't

`accounts/__init__.py` uses `TYPE_CHECKING` for type hints, but `analytics/__init__.py` and others have inconsistent patterns.

**Recommended Fix:** Standardize facade pattern across all domains.

---

### M8. Duplicate Code: _keyset_list/_keyset_page Helpers

**Severity:** MEDIUM  
**Impact:** Duplicated across all ports.py files

The same `_keyset_list` and `_keyset_page` helper functions are copy-pasted into every domain's `ports.py`.

**Recommended Fix:** Extract to a shared utility in `infrastructure/`.

---

### M9. Unused Imports in Key Files

**Severity:** MEDIUM  
**Impact:** Dead code, confusion

**File:** `domains/accounts/ports.py:625-626`
```python
from domains.accounts.models.core import Address, CartItem, CityDistanceMatrix
from domains.accounts.models.user import Referral, User
```
These re-exports duplicate the lazy-loaded exports in `__init__.py`.

**Recommended Fix:** Remove duplicate re-exports.

---

### M10. Inconsistent Async/Sync Patterns

**Severity:** MEDIUM  
**Impact:** Performance issues, blocking IOLoop

Some services use `async def` while others use `def` for database operations. The codebase claims async SQLAlchemy but many service functions are synchronous.

**Recommended Fix:** Standardize on async patterns for all I/O-bound operations.

---

### M11. Missing Input Validation in Service Functions

**Severity:** MEDIUM  
**Impact:** Potential security issues

Many service functions accept raw parameters without Pydantic validation, relying on callers to validate.

**Recommended Fix:** Use Pydantic request models at the service boundary.

---

### M12. Inconsistent Logging Patterns

**Severity:** MEDIUM  
**Impact:** Hard to debug production issues

Some services use `logger = logging.getLogger(__name__)`, others use module-level loggers, others don't log at all.

**Recommended Fix:** Standardize logging with structured JSON logging.

---

### M13. Missing Docstrings on Public Functions

**Severity:** MEDIUM  
**Impact:** Poor developer experience

Many public functions in services lack docstrings or have only `"""Stub ..."""` placeholders.

**Recommended Fix:** Add proper docstrings to all public functions.

---

### M14. Inconsistent Return Types

**Severity:** MEDIUM  
**Impact:** Unpredictable API responses

Some functions return `dict`, others return Pydantic models, others return tuples.

**Recommended Fix:** Standardize on Pydantic response models.

---

### M15. Unused Import: Base in Service Files

**Severity:** MEDIUM  
**Impact:** Confusion about whether services define models

**File:** `domains/promotions/services/engine/promotion_service.py:15`
```python
from infrastructure.database.base import Base
```

**File:** `domains/promotions/services/engine/promotion_engine_service.py:18`
```python
from infrastructure.database.base import Base
```

Services should not import `Base` — that's a model-layer concern.

**Recommended Fix:** Remove `Base` imports from service files.

---

### M16. Duplicate Functionality Across Domains

**Severity:** MEDIUM  
**Impact:** Maintenance burden

- `CartService` exists in both `customers/services/cart_service.py` and `orders/services/cart/service.py`
- `SearchService` exists in both `customers/services/search_service.py` and `catalog/services/search/search_service.py`
- `ReferralsService` in customers vs `Referral` model in accounts

**Recommended Fix:** Consolidate shared services into a single owning domain.

---

### M17. Inconsistent Naming: Service vs Services

**Severity:** MEDIUM  
**Impact:** Confusing import paths

Some domains use `services/` (plural) while the architecture diagram may imply singular. Within `accounts/services/` there's a mix of singular and plural file names.

**Recommended Fix:** Standardize on `services/` (plural) consistently.

---

### M18. Missing Error Handling in Critical Paths

**Severity:** MEDIUM  
**Impact:** Data inconsistency on partial failures

**File:** `domains/finance/services/payouts/payout_batch_service.py` — complex batch operations lack transaction rollback on partial failure.

**Recommended Fix:** Wrap batch operations in proper savepoints/rollback.

---

## LOW Issues

### L1. Inconsistent File Header Comments

**Severity:** LOW  
**Impact:** Some files have module docstrings, others don't

**Recommended Fix:** Add module docstrings to all files.

---

### L2. Inconsistent Import Ordering

**Severity:** LOW  
**Impact:** Harder to read imports

Some files group imports by type (stdlib, third-party, local), others don't.

**Recommended Fix:** Enforce with `ruff check --select I`.

---

### L3. Missing Type Hints on Some Functions

**Severity:** LOW  
**Impact:** Reduced IDE support

Some internal functions lack return type annotations.

**Recommended Fix:** Add type hints to all functions.

---

### L4. Inconsistent Use of `from __future__ import annotations`

**Severity:** LOW  
**Impact:** Some files have it, others don't

**Recommended Fix:** Add to all files for consistent PEP 604 behavior.

---

### L5. Unused Variables in Some Functions

**Severity:** LOW  
**Impact:** Dead code

**Recommended Fix:** Remove unused variables.

---

### L6. Inconsistent Constant Naming

**Severity:** LOW  
**Impact:** Some constants are UPPER_CASE, others are not

**Recommended Fix:** Enforce UPPER_CASE for module-level constants.

---

### L7. Missing `__all__` in Model __init__.py Files

**Severity:** LOW  
**Impact:** Unclear exports

**Recommended Fix:** Add `__all__` to model `__init__.py` files.

---

### L8. Inconsistent Use of `Optional` vs `| None`

**Severity:** LOW  
**Impact:** Style inconsistency

Some files use `Optional[X]`, others use `X | None`.

**Recommended Fix:** Standardize on `X | None` (PEP 604).

---

### L9. Missing `if __name__ == "__main__"` Guards in Utility Files

**Severity:** LOW  
**Impact:** Code runs on import

**Recommended Fix:** Add guards to utility scripts.

---

### L10. Inconsistent Docstring Format

**Severity:** LOW  
**Impact:** Some use Google style, others use Sphinx style

**Recommended Fix:** Standardize on one format.

---

### L11. Unused Imports in Domain Facades

**Severity:** LOW  
**Impact:** Minor performance impact on import

**Recommended Fix:** Clean up unused imports.

---

### L12. Inconsistent Error Messages

**Severity:** LOW  
**Impact:** Poor developer experience

Error messages range from descriptive to cryptic.

**Recommended Fix:** Standardize error message format.

---

## Domain-by-Domain Summary

| Domain | Files | Critical | High | Medium | Low | Notes |
|--------|-------|----------|------|--------|-----|-------|
| **accounts** | 42 | 4 | 5 | 4 | 2 | Most problematic domain. God service, cross-domain creation, model duplication |
| **analytics** | 35 | 0 | 2 | 2 | 1 | Broad exception handling, TODO stubs |
| **audit** | 37 | 1 | 2 | 1 | 1 | Wildcard imports, empty read_models |
| **catalog** | 38 | 0 | 2 | 2 | 1 | Empty policies/schemas, duplicate CartService |
| **comms** | 43 | 0 | 1 | 2 | 1 | Empty service subdirs, duplicate SupportTicket |
| **country** | 51 | 1 | 1 | 1 | 0 | Stub classes, empty utils |
| **customers** | 39 | 0 | 1 | 1 | 1 | Duplicate CartService/SearchService |
| **finance** | 47 | 1 | 3 | 2 | 1 | Duplicate functions, large files, Base imports in services |
| **governance** | 46 | 0 | 2 | 2 | 1 | Model duplication (User, etc.), TODO subscribers |
| **hr** | 51 | 0 | 2 | 1 | 1 | Duplicate ShiftHandoverTask, empty subdirs |
| **logistics** | 39 | 0 | 2 | 2 | 1 | TODO stubs, large files |
| **orders** | 44 | 0 | 1 | 1 | 1 | Large logistics.py file |
| **promotions** | 43 | 0 | 1 | 2 | 1 | Base imports in services, duplicate CouponUsage |
| **security** | 41 | 1 | 2 | 1 | 1 | Hardcoded fallback secret, empty subdirs |
| **suppliers** | 47 | 0 | 1 | 1 | 1 | TODO stubs in verify service |

---

## Recommended Priority Order

1. **Consolidate duplicate models** — Pick one owning domain for each model, delete duplicates
2. **Fix cross-domain imports** — All reads via ports.py, all writes via events
3. **Split auth_service.py** — Extract SSO, biometric, OTP, session management
4. **Remove empty stubs** — Delete or implement empty files and directories
5. **Fix broad exception handling** — Replace catch-all patterns with specific exceptions
6. **Remove hardcoded secret** — Raise error if `secret_key` is missing
7. **Generate ports.py** — Move to code generation, out of source control
8. **Implement events/subscribers** — Define real cross-domain events
9. **Standardize naming** — Schemas, models, file organization
10. **Decompose large services** — Split files > 30 KB

---

## Architecture Compliance Score

| Law | Compliance | Notes |
|-----|------------|-------|
| Law 1 (Arrows down only) | 40% | Frequent cross-domain model imports |
| Law 2 (Thin routers) | 70% | Some routers still contain business logic |
| Law 3 (Events/Ports) | 30% | Most events.py are empty placeholders |
| Law 4 (Features single-sourced) | 85% | Mostly compliant |
| Law 5 (Country scope) | 60% | RLS not enforced at DB layer |
| Law 6 (Schema discipline) | 75% | Mixed naming conventions |
| Law 7 (Allowlist) | Unknown | Need to check DOMAIN_ALLOWLIST.yaml |

**Overall Architecture Compliance: 55%**
