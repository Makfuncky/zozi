# ZOZI Backend — Accounts Domain: Complete Problem Diagnosis

> **Date:** 2026-08-26
> **Scope:** `backend/domains/accounts/` — Every file, every function
> **Reference:** ARCHITECTURE_DIAGRAM.md (The Seven Laws)
> **Total Problems Found:** 87

---

## Executive Summary

The `accounts` domain is the **most problematic domain** in the ZOZI backend. It suffers from:

1. **Massive cross-domain contamination** — imports from 13 other domains
2. **Oversized files** — `auth_service.py` is 2,793+ lines (5.6x threshold)
3. **Wrong-domain services** — logistics, HR, and security services in accounts
4. **Model ownership chaos** — 30+ tables from other domains defined in accounts
5. **Empty events/subscribers** — despite heavy cross-domain writes
6. **Broken RBAC** — `DEFAULT_ROLE_PERMISSION_MAP = {}` makes all permissions empty

---

## 1. CRITICAL Problems (12)

### CRIT-001: `auth_service.py` directly creates `SupplierProfile` (Law 3 violation)

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 2341-2361 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3: Cross-domain writes only via events |

**Current Code:**
```python
# In register_user() function
supplier_profile = SupplierProfile(
    user_id=db_user.id,
    company_name=body.get("company_name", ""),
    # ... more fields
)
db.add(supplier_profile)
db.commit()
```

**Problem:** Auth service directly creates `SupplierProfile` which belongs to the suppliers domain. This is a cross-domain write without using events.

**Solution:**
```python
# In auth_service.py - emit event instead
from domains.accounts.events import UserCreatedEvent
# ... after user creation
event = UserCreatedEvent(
    user_id=db_user.id,
    role=role,
    company_name=body.get("company_name"),
)
event_bus.publish(event)
```

---

### CRIT-002: `auth_service.py` directly creates `LogisticsPartner` (Law 3 violation)

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 2362-2374 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3: Cross-domain writes only via events |

**Current Code:**
```python
# In register_user() function
logistics_partner = LogisticsPartner(
    user_id=db_user.id,
    # ... more fields
)
db.add(logistics_partner)
db.commit()
```

**Problem:** Direct cross-domain write to logistics domain.

**Solution:** Emit `UserCreatedEvent` and let logistics domain subscriber create the partner record.

---

### CRIT-003: `identity_admin_service.py` calls undefined functions

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/identity/identity_admin_service.py` |
| **Lines** | 183-190 |
| **Severity** | CRITICAL |

**Current Code:**
```python
def admin_update_user_role(user_id: int, role: str, acting_user: dict, db: Session):
    return update_user_role(user_id, role, acting_user, db)  # NOT IMPORTED!

def admin_toggle_user_active(user_id: int, acting_user: dict, db: Session):
    return toggle_user_active(user_id, acting_user, db)  # NOT IMPORTED!
```

**Problem:** `update_user_role` and `toggle_user_active` are not imported. This will raise `NameError` at runtime.

**Solution:**
```python
# Add imports at top of file
from domains.accounts.services.users.users_admin_service import (
    update_user_role,
    toggle_user_active,
)
```

---

### CRIT-004: `models/core.py` defines 30+ tables from other domains

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/core.py` |
| **Lines** | 28-48 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 6: Schema discipline |

**Current Code:**
```python
__all__ = [
    "Address", "Cart", "CartItem", "UserBrowsingHistory", "UserSession", "SystemHealthDevice",
    # Below are from OTHER domains:
    "AuditLog", "SupportTicket", "SupportTicketReply", "TicketAttachment",
    "CityDistanceMatrix", "ExecutiveNews", "NewsSource", "InternalNotice",
    "PredictiveSimulation", "AlertEscalationRule", "NewsArticle",
    "DirectChatMessage", "DirectChatRoom", "EntityChatMessage", "EntityChatThread",
    "GroupChatRoom", "GroupChatMember", "GroupChatMessage", "VideoRoom",
    "VideoRoomParticipant", "VideoRoomRecording", "ShiftHandoverSession",
    "ShiftHandoverTask", "EscalationSLALog",
]
```

**Problem:** These tables belong to comms, logistics, analytics, security, audit, hr, and catalog domains.

**Solution:** Remove all non-accounts models. accounts/core.py should only own:
- `Address`, `Cart`, `CartItem`, `UserBrowsingHistory`, `UserSession`, `SystemHealthDevice`

---

### CRIT-005: `logistics_partner_service.py` star-imports from logistics domain

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/logistics_partner_service.py` |
| **Line** | 2 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 1: Arrows point down only |

**Current Code:**
```python
from domains.logistics.services.partners.logistics_partner_service import *
```

**Problem:** Star import from another domain's service. This is a logistics service in accounts domain.

**Solution:** Delete this file. Consumers should import from `domains.logistics.services.partners.logistics_partner_service` directly.

---

### CRIT-006: `ports.py` imports from `domains.security.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/ports.py` |
| **Line** | 34 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3: Cross-domain reads only via ports |

**Current Code:**
```python
from domains.security.models.security_schema_models import AlertEscalationRule, DocumentVerification, KYCVerification
```

**Problem:** Direct cross-domain model import at module level.

**Solution:** Remove these imports. Use `domains.security.ports` for reading security models.

---

### CRIT-007: `auth_service.py` imports from `domains.comms.models` and `domains.logistics.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 1402-1412 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3 |

**Current Code:**
```python
from domains.comms.models.suppliers import SupplierProfile
from domains.logistics.models.logistics import LogisticsPartner
from domains.finance.models.payments import ...
```

**Problem:** Auth service directly imports from comms, logistics, and finance models.

**Solution:** Remove these imports. Use events for cross-domain writes.

---

### CRIT-008: `users_admin_service` split files import 15+ domains

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/users/users_admin_service/__header___p1_p1.py` |
| **Lines** | 10-78 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 1, Law 3 |

**Current Code:**
```python
from domains.governance.models.core import ...
from domains.governance.models.user import ...
from domains.catalog.models.products import ...
from domains.comms.models.communication import ...
from domains.comms.models.marketing import ...
from domains.comms.models.suppliers import ...
from domains.finance.models.commission import ...
from domains.finance.models.finance import ...
from domains.governance.models.admin import ...
from domains.logistics.models.logistics import ...
from domains.orders.models.orders import ...
from domains.catalog.models.promotions import ...
from domains.finance.models.payments import ...
```

**Problem:** This file alone imports from 13 other domains.

**Solution:** Delete these split files. Consolidate into a single `users_admin_service.py` that only depends on `domains.governance.ports`.

---

### CRIT-009: `auth_service.py` uses `SessionLocal` directly

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains\accounts\services\auth\auth_service.py` |
| **Lines** | 46, 292, 413, 467, 527, 640, 692, 918, 1124, 1154 |
| **Severity** | CRITICAL |

**Current Code:**
```python
from infrastructure.database.database import SessionLocal
# ...
db = SessionLocal()
```

**Problem:** Services should not create their own DB sessions. Breaks testability and transaction management.

**Solution:** Remove `SessionLocal` usage. All functions should accept `db: Session` as parameter.

---

### CRIT-010: `events.py` is an empty placeholder

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/events.py` |
| **Line** | 7 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3 |

**Current Code:**
```python
# TODO: Define accounts-domain events here when cross-domain write needs arise.
```

**Problem:** Despite heavy cross-domain coupling, no events exist.

**Solution:** Define events:
```python
@dataclass(frozen=True)
class UserCreatedEvent(DomainEvent):
    user_id: int = 0
    role: str = ""
    company_name: str = ""

@dataclass(frozen=True)
class UserRoleChangedEvent(DomainEvent):
    user_id: int = 0
    old_role: str = ""
    new_role: str = ""
```

---

### CRIT-011: `subscribers.py` is an empty placeholder

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/subscribers.py` |
| **Line** | 7 |
| **Severity** | CRITICAL |
| **Law Violated** | Law 3 |

**Current Code:**
```python
# TODO: Define accounts-domain subscribers here when cross-domain reactions are needed.
```

**Problem:** No subscribers despite cross-domain writes happening directly.

**Solution:** Define subscribers for accounts events in other domains.

---

### CRIT-012: `permission_service.py` RBAC is broken

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/permissions/permission_service.py` |
| **Lines** | 449, 461-467 |
| **Severity** | CRITICAL |

**Current Code:**
```python
DEFAULT_ROLE_PERMISSION_MAP: dict = {}  # Hardcoded empty!
DEFAULT_ROLES = {role: {"permissions": sorted(permissions)} for role, permissions in DEFAULT_ROLE_PERMISSION_MAP.items()}
```

**Problem:** The map is hardcoded to empty dict. So `DEFAULT_ROLES` is always `{}` and `get_user_permissions()` always returns `[]`.

**Solution:**
```python
from infrastructure.utils.staff_permissions import DEFAULT_ROLE_PERMISSION_MAP
```

---

## 2. HIGH Problems (28)

### HIGH-001: `auth_service.py` is 2,793+ lines

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | All |
| **Severity** | HIGH |

**Problem:** Contains 5 auth doors, OTP, registration, social login, referrals — all in one file.

**Solution:** Split into:
- `auth/password_service.py`
- `auth/otp_service.py`
- `auth/biometric_service.py`
- `auth/sso_service.py`
- `auth/registration_service.py`
- `auth/token_service.py`
- `auth/referral_service.py`

---

### HIGH-002: `accounts_service.py` is dead code

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/accounts_service.py` |
| **Severity** | HIGH |

**Problem:** All functions wrap HR service calls. No unique logic.

**Solution:** Delete this file. Routers should call HR services directly.

---

### HIGH-003: `logistics_partner_service.py` is dead code

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/logistics_partner_service.py` |
| **Severity** | HIGH |

**Problem:** Just a star import re-export. No logic.

**Solution:** Delete this file.

---

### HIGH-004: `identity_admin_service.py` duplicates security domain

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/identity/identity_admin_service.py` |
| **Severity** | HIGH |

**Problem:** User lifecycle operations are security/governance domain concerns.

**Solution:** Move to `domains.security.services` or `domains.governance.services`.

---

### HIGH-005: `permission_service.py` duplicates rbac/ domain

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/permissions/permission_service.py` |
| **Severity** | HIGH |

**Problem:** Contains `RBACService` class that duplicates `rbac/` domain functionality.

**Solution:** Move RBAC service to `domains.rbac.services` or `domains.governance.services`.

---

### HIGH-006: `Cart`/`CartItem` models in accounts

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/core.py` |
| **Lines** | 74-103 |
| **Severity** | HIGH |

**Problem:** Shopping cart belongs to catalog/orders domain.

**Solution:** Move to `domains.catalog.models.cart` or `domains.orders.models.cart`.

---

### HIGH-007: Chat models in accounts

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/core.py` |
| **Lines** | 124-134 |
| **Severity** | HIGH |

**Problem:** `DirectChatMessage`, `GroupChatRoom`, etc. belong to comms domain.

**Solution:** Remove from accounts. Already defined in comms domain.

---

### HIGH-008: `SupportTicket` models in accounts

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/core.py` |
| **Severity** | HIGH |

**Problem:** Support tickets belong to comms domain.

**Solution:** Remove from accounts.

---

### HIGH-009: `AuditLog` in accounts

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/core.py` |
| **Line** | 110 |
| **Severity** | HIGH |

**Problem:** AuditLog belongs to audit domain.

**Solution:** Remove from accounts.

---

### HIGH-010: `ports.py` re-exports 30+ models from other domains

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/ports.py` |
| **Lines** | 29-33 |
| **Severity** | HIGH |

**Problem:** ports.py has become a dumping ground for cross-domain model access.

**Solution:** ports.py should only expose accounts-domain models and functions.

---

### HIGH-011: `auth_service.py` imports from `domains.hr.ports`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Line** | 50 |
| **Severity** | HIGH |

**Current Code:**
```python
from domains.hr.ports import Employee, EmployeeBiometric, DynamicQRSession, GeoFenceLog, EmployeeAttendance
```

**Problem:** Auth service should not depend on HR models.

**Solution:** Remove these imports. HR-specific logic belongs in HR domain.

---

### HIGH-012: `auth_service.py` imports from `domains.finance.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 1404-1412 |
| **Severity** | HIGH |

**Problem:** Direct finance model imports.

**Solution:** Remove these imports.

---

### HIGH-013: `models/onboarding.py` imports from `domains.security.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/models/onboarding.py` |
| **Line** | 10 |
| **Severity** | HIGH |

**Current Code:**
```python
from domains.security.models.security_schema_models import DocumentVerification, KYCVerification
```

**Problem:** Module-level cross-domain model import.

**Solution:** Remove the import. Use lazy `__getattr__` for backward compat.

---

### HIGH-014: `services/accounts_service.py` imports from `domains.hr.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/accounts_service.py` |
| **Line** | 10 |
| **Severity** | HIGH |

**Problem:** Direct HR model import.

**Solution:** Delete this file.

---

### HIGH-015: `services/tracker/live_session_tracker.py` imports from `domains.hr.models`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/tracker/live_session_tracker.py` |
| **Line** | 152 |
| **Severity** | HIGH |

**Problem:** Direct HR model import inside a function.

**Solution:** Use `domains.hr.ports` for reading HR models.

---

### HIGH-016: `users_admin_service` split files have 60+ lines of identical imports

| Attribute | Value |
|-----------|-------|
| **File** | All `__header___*.py` files in `users_admin_service/` |
| **Severity** | HIGH |

**Problem:** Each file repeats the exact same 60+ import lines.

**Solution:** Consolidate into a single file.

---

### HIGH-017: `merged_from_user_write_ops_py.py` duplicates constants

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/users/users_admin_service/merged_from_user_write_ops_py.py` |
| **Lines** | 127-210 |
| **Severity** | HIGH |

**Problem:** Same constants defined in two files.

**Solution:** Consolidate into a single file.

---

### HIGH-018: `list_staff_accounts()` has no pagination

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/users/users_admin_service/__header___p1_p1.py` |
| **Lines** | 120-128 |
| **Severity** | HIGH |

**Current Code:**
```python
.limit(200).all()  # hardcoded limit
```

**Problem:** Will break at scale.

**Solution:** Add cursor-based pagination.

---

### HIGH-019: `list_all_users()` uses OFFSET pagination

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/identity/identity_admin_service.py` |
| **Lines** | 84-86 |
| **Severity** | HIGH |

**Current Code:**
```python
db.query(User).offset(skip).limit(limit).all()
```

**Problem:** OFFSET pagination is forbidden on hot lists.

**Solution:** Use keyset (cursor) pagination.

---

### HIGH-020: `users_admin_service` N+1 in `get_all_users()`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/users/users_admin_service/__header___p1_p1.py` |
| **Lines** | 142-146 |
| **Severity** | HIGH |

**Problem:** N+1 pattern — users query + profiles query.

**Solution:** Use `selectinload` or `joinedload` for profiles.

---

### HIGH-021: `auth_service.py` N+1 in registration

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Line** | 2403 |
| **Severity** | HIGH |

**Problem:** After creating user, re-queries with `db.query(User).filter(User.id == created_user_id).first()`.

**Solution:** Use the already-loaded `db_user` object directly.

---

### HIGH-022: `auth_service.py` swallows exceptions in `_get_redis()`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 85-86 |
| **Severity** | HIGH |

**Current Code:**
```python
except Exception: return None
```

**Problem:** All Redis errors silently ignored.

**Solution:**
```python
except Exception as e:
    logger.warning("Redis connection failed: %s", e)
    return None
```

---

### HIGH-023: `auth_service.py` swallows exceptions in `logout()`

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Line** | 1177 |
| **Severity** | HIGH |

**Problem:** Token blacklisting failure is silently logged but the function still returns success.

**Solution:** Consider re-raising or returning an error status.

---

### HIGH-024: `auth_service.py` has duplicate token issuance logic

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 1868-1982 |
| **Severity** | HIGH |

**Problem:** `_issue_auth_tokens()` and `_create_tokens_response()` are nearly identical.

**Solution:** Consolidate into a single function.

---

### HIGH-025: `auth_service.py` has duplicate user payload logic

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/auth/auth_service.py` |
| **Lines** | 1700-1764 |
| **Severity** | HIGH |

**Problem:** `_user_public_payload()` and inline payload in `get_current_user()` are nearly identical.

**Solution:** Use `_user_public_payload()` everywhere.

---

### HIGH-026: `permission_service.py` is 750 lines

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/permissions/permission_service.py` |
| **Severity** | HIGH |

**Problem:** Contains permission CRUD, role-permission assignments, user overrides, RBACService class.

**Solution:** Split into: `permission_service.py`, `rbac_service.py`, `delegation_service.py`.

---

### HIGH-027: `ports.py` is 628 lines

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/ports.py` |
| **Severity** | HIGH |

**Problem:** 628 lines of repetitive get/list functions for 30+ models.

**Solution:** Remove cross-domain re-exports. Only expose accounts-domain models.

---

### HIGH-028: `users_admin_service/__header___p2_p1.py` is 490 lines

| Attribute | Value |
|-----------|-------|
| **File** | `backend/domains/accounts/services/users/users_admin_service/__header___p2_p1.py` |
| **Severity** | HIGH |

**Problem:** Contains bulk operations, CRUD, bank account management.

**Solution:** Consolidate into a single `users_admin_service.py` file.

---

## 3. MEDIUM Problems (32)

| # | File | Line | Problem | Solution |
|---|------|------|---------|----------|
| MED-001 | `features.py` | 6-10 | Only 3 features defined | Add `accounts.auth.login`, `accounts.auth.mfa`, etc. |
| MED-002 | `models/core.py` | 18 | `from . import Base` | `from infrastructure.database.base import Base` |
| MED-003 | `permission_service.py` | 38 | Bare `except AttributeError` | Add logging |
| MED-004 | `auth_service.py` | 2403 | N+1 in registration | Use already-loaded object |
| MED-005 | `auth_service.py` | 960 | SSO sets role to department | Map departments to roles |
| MED-006 | `auth_service.py` | 602-621 | Face encoding is demo | Integrate proper face recognition |
| MED-007 | `CityDistanceMatrix` | 120 | In accounts, belongs to logistics | Remove |
| MED-008 | `ExecutiveNews` | 121 | In accounts, belongs to analytics | Remove |
| MED-009 | `AlertEscalationRule` | 122 | In accounts, belongs to security | Remove |
| MED-010 | `ShiftHandoverSession` | 135 | In accounts, belongs to HR | Remove |
| MED-011 | `users_admin_service` | All | No `__init__.py` exports | Add proper exports |
| MED-012 | `schemas/__init__.py` | All | Empty file | Add exports |
| MED-013 | `permission_service.py` | 327 | Missing `db.rollback()` | Add rollback in except block |
| MED-014 | `identity_admin_service.py` | 84-86 | OFFSET pagination | Use keyset pagination |
| MED-015 | `__header___p1_p1.py` | 120-128 | Hardcoded limit 200 | Add cursor pagination |
| MED-016-032 | Various | Various | Various code quality issues | Apply standard fixes |

---

## 4. LOW Problems (15)

| # | File | Problem | Solution |
|---|------|---------|----------|
| LOW-001 | `utils/__init__.py` | Empty file | Delete |
| LOW-002 | `_PROTECTED_EMAILS` | Hardcoded set | Move to settings |
| LOW-003 | `permission_service.py:38` | Bare `except AttributeError` | Add logging |
| LOW-004 | `users_admin_service` | No `__init__.py` in `services/users/` | Add exports |
| LOW-005 | `schemas/__init__.py` | Empty | Add exports |
| LOW-006-015 | Various | Various style issues | Apply standard fixes |

---

## 5. Summary of Required Actions

### Immediate (CRITICAL)
1. Delete `logistics_partner_service.py`
2. Delete `accounts_service.py`
3. Delete `users_admin_service/` split files
4. Remove cross-domain models from `models/core.py`
5. Add missing imports to `identity_admin_service.py`
6. Fix `permission_service.py` RBAC
7. Define events in `events.py`
8. Define subscribers in `subscribers.py`
9. Remove cross-domain imports from `auth_service.py`
10. Remove cross-domain imports from `ports.py`

### Short-term (HIGH)
1. Split `auth_service.py` into 8 focused services
2. Split `permission_service.py` into 3 services
3. Move `identity_admin_service.py` to security/governance
4. Move `Cart`/`CartItem` to catalog/orders
5. Add pagination to all list functions
6. Fix N+1 query patterns
7. Fix exception swallowing

### Medium-term (MEDIUM)
1. Expand `features.py`
2. Fix schema references
3. Add missing error handling
4. Consolidate split files

---

*End of Diagnosis Report*
