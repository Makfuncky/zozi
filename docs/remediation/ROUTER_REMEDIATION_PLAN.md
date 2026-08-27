# ZOZI Backend Router Remediation Plan — Accurate State

> **Generated:** 2026-08-27 (detailed line-by-line investigation)  
> **Scope:** 75 router files across 5 modules  
> **Architecture Ref:** `ARCHITECTURE_DIAGRAM.md`  

---

## 1. Current State Summary

### ✅ What's Fixed

| Metric | Status |
|---|---|
| **DB calls in routers** | ✅ **0** — all routers thin |
| **Employee subdirectories** | ✅ **DELETED** — flat structure |
| **Pydantic models inline** | 89 (down from 115) |

### ❌ What's Broken (Code Won't Run)

| Issue | Files | Count |
|---|---|---|
| **_auto_stubs imports** | 6 files | 47 imports |
| **Undefined references** | 4 files | 27 references |
| **Imports from non-existent files** | 1 file | 103 references |

### ❌ What Needs Cleanup

| Issue | Files | Count |
|---|---|---|
| **Cross-module imports** | 5 files | 32 imports |
| **Duplicate routes** | 4 files | 75 routes |
| **Pydantic models inline** | 6 files | 89 models |
| **Colon-feature strings** | 1 file | 19 strings |

---

## 2. Module: Admin — Problems & Fixes

### 2.1 `country.py` (353 lines) — 🔴 21 Undefined References

| Missing Function | Line Used | Fix |
|---|---|---|
| `svc_list_cities` | L81 | `from domains.country.services.core.country_service import list_cities as svc_list_cities` |
| `svc_add_city` | L97 | `from domains.country.services.core.country_service import add_city as svc_add_city` |
| `svc_update_city` | L124 | `from domains.country.services.core.country_service import update_city as svc_update_city` |
| `svc_delete_city` | L146 | `from domains.country.services.core.country_service import delete_city as svc_delete_city` |
| `svc_list_staff` | L156 | `from domains.country.services.staff.country_staff_service import list_staff as svc_list_staff` |
| `svc_assign_staff` | L168 | `from domains.country.services.staff.country_staff_service import assign_staff as svc_assign_staff` |
| `svc_remove_staff` | L179 | `from domains.country.services.staff.country_staff_service import remove_staff as svc_remove_staff` |
| `svc_list_tax_rates` | L189 | `from domains.country.services.tax.tax_service import list_tax_rates as svc_list_tax_rates` |
| `svc_set_tax_rate` | L202 | `from domains.country.services.tax.tax_service import set_tax_rate as svc_set_tax_rate` |
| `svc_send_country_communication` | L225 | `from domains.country.services.core.country_service import send_country_communication as svc_send_country_communication` |
| `svc_list_communications` | L247 | `from domains.country.services.core.country_service import list_communications as svc_list_communications` |
| `svc_mark_communication_read` | L257 | `from domains.country.services.core.country_service import mark_communication_read as svc_mark_communication_read` |
| `svc_toggle_country_active` | L267 | `from domains.country.services.core.country_service import toggle_country_active as svc_toggle_country_active` |
| `svc_archive_country` | L277 | `from domains.country.services.core.country_service import archive_country as svc_archive_country` |
| `svc_restore_country` | L287 | `from domains.country.services.core.country_service import restore_country as svc_restore_country` |
| `svc_bulk_archive_countries` | L297 | `from domains.country.services.core.country_service import bulk_archive_countries as svc_bulk_archive_countries` |
| `svc_bulk_restore_countries` | L307 | `from domains.country.services.core.country_service import bulk_restore_countries as svc_bulk_restore_countries` |
| `svc_hard_delete_country` | L317 | `from domains.country.services.core.country_service import hard_delete_country as svc_hard_delete_country` |
| `svc_list_country_commission_rates` | L328 | `from domains.country.services.core.country_service import list_country_commission_rates as svc_list_country_commission_rates` |
| `svc_create_country_commission_rate` | L339 | `from domains.country.services.core.country_service import create_country_commission_rate as svc_create_country_commission_rate` |
| `svc_delete_country_commission_rate` | L351 | `from domains.country.services.core.country_service import delete_country_commission_rate as svc_delete_country_commission_rate` |

**Action:** Add imports at top of file (lines 11-17 area).

### 2.2 `customers.py` (128 lines) — 🔴 2 Undefined References

| Missing Function | Line | Fix |
|---|---|---|
| `get_wishlist` | L99 | `from domains.customers.services.wishlist_service import get_wishlist, clear_user_wishlist` |
| `clear_user_wishlist` | L128 | (same import as above) |

**Action:** Add import at line 14.

### 2.3 `orders.py` (87 lines) — 🔴 1 Undefined Reference

| Missing Function | Line | Fix |
|---|---|---|
| `email_metrics` | L32 | `from domains.comms.services.email.email_management import get_email_metrics as email_metrics` |

**Action:** Add import at line 17.

### 2.4 `hr.py` (254 lines) — 6 Inline Pydantic Models

| Model | Line | Move To |
|---|---|---|
| `ExpenseSubmitRequest` | L31 | `domains/hr/schemas/requests.py` |
| `AddressRequest` | L39 | `domains/hr/schemas/requests.py` |
| `DependentRequest` | L48 | `domains/hr/schemas/requests.py` |
| `COIReportRequest` | L54 | `domains/hr/schemas/requests.py` |
| `DisciplinaryCaseRequest` | L60 | `domains/hr/schemas/requests.py` |
| `OffboardingCaseRequest` | L66 | `domains/hr/schemas/requests.py` |

**Action:** Create `domains/hr/schemas/requests.py` and import from there.

### 2.5 `security.py` (214 lines) — 3 Inline Pydantic Models

| Model | Line | Move To |
|---|---|---|
| `FraudScoreRequest` | L34 | `domains/security/schemas/requests.py` |
| `BlacklistCreateRequest` | L43 | `domains/security/schemas/requests.py` |
| `RuleCreateRequest` | L50 | `domains/security/schemas/requests.py` |

### 2.6 `analytics.py` (15 lines) — Needs Routes

**Add thin delegators to `domains/analytics/services/flat_admin_dashboard_service.py`:**
```python
from domains.analytics.services.flat_admin_dashboard_service import (
    admin_dashboard_fallback, admin_stats_fallback, admin_payouts_fallback,
    admin_commission_fallback, admin_employees_fallback, admin_payments_fallback,
    admin_logistics_fallback, admin_logistics_partners_fallback,
    admin_treasury_fallback, admin_treasury_metrics_fallback,
)

@router.get("/dashboard")
def dashboard(db=Depends(get_db), _=Depends(require_admin)):
    require_feature("analytics.dashboard.view")
    return admin_dashboard_fallback(db)

@router.get("/stats")
def stats(db=Depends(get_db), _=Depends(require_admin)):
    require_feature("analytics.read")
    return admin_stats_fallback(db)

@router.get("/payouts")
def payouts(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_db), _=Depends(require_admin)):
    require_feature("analytics.reports.read")
    return admin_payouts_fallback(db, page=page, page_size=page_size)

# ... etc for remaining 7 functions
```

---

## 3. Module: Customer — Problems & Fixes

### 3.1 `comms.py` (48 lines) — 🔴 1 _auto_stubs Import

| Line | Broken Import | Fix |
|---|---|---|
| L15 | `from domains.comms.services._auto_stubs import TranslationService` | `from domains.comms.services.translation.translation_service import TranslationService` |

### 3.2 `finance.py` (357 lines) — 🔴 3 Undefined References

| Missing Symbol | Line | Fix |
|---|---|---|
| `confirm_thawani_payment` | L261 | Import from `domains.finance.services.payments.gateway_thawani` or remove call |
| `User` | L351 | `from domains.governance.models.user import User` |
| `get_current_user_orch` | L351 | Import or replace with `get_current_user` |

### 3.3 `customers.py` (117 lines) — ⚠️ 2 Duplicate Function Definitions

| Function | Lines | Fix |
|---|---|---|
| `get_customer_health` | L23, L57, L98 | Keep only L98, delete L23-30 and L57-64 |
| `list_customer_health` | L34, L68, L109 | Keep only L109, delete L34-41 and L68-75 |

### 3.4 `orders.py` (313 lines) — ⚠️ 1 Duplicate Route + Inline Models

| Issue | Lines | Fix |
|---|---|---|
| `GET /` defined twice | L39 (`get_cart`), L260 (`list_returns`) | Rename second to `GET /returns` |
| `POST /` defined twice | L81 (`clear_cart`), L266 (`create_return`) | Rename second to `POST /returns` |
| `CartItemUpdate` inline | L33 | Move to `domains/customers/schemas/cart.py` |
| `BulkReturnStatusUpdateBody` inline | L222 | Move to `domains/customers/schemas/orders.py` |

### 3.5 `promotions.py` (442 lines) — ⚠️ 11 Duplicate Routes + 3 Inline Models

| Issue | Lines | Fix |
|---|---|---|
| `POST /validate` × 3 | L71, L170, L258 | Keep only L258, delete L71-122 and L170-256 |
| `GET /` × 4 | L87, L197, L273, L333 | Keep only L333, delete earlier |
| `POST /` × 3 | L93, L208, L284 | Keep only L284, delete earlier |
| `DELETE /{coupon_id}` × 2 | L105, L228 | Keep only L228, delete L105 |
| `CouponValidateBody` inline | L140 | Move to `domains/customers/schemas/coupons.py` |
| `CouponValidateView` inline | L146 | Move to `domains/customers/schemas/cromotions.py` |
| `CouponView` inline | L153 | Move to `modules/customer/serializers/promotions.py` |
| 6 helpers inline | L28-64 | Move to `domains/customers/services/coupons_service.py` |

**Action:** Delete duplicate blocks, move models to schemas, use existing `coupons_service.py`.

---

## 4. Module: Employee — Problems & Fixes

### 4.1 `comms.py` (1572 lines) — 🔴 29 _auto_stubs Imports

| Line | Broken Import | Fix |
|---|---|---|
| L164 | `from domains.comms.services._auto_stubs import VideoConferenceRoom` | `from domains.comms.services.video.video_models import VideoConferenceRoom` |
| L165 | `from domains.comms.services._auto_stubs import get_video_conference` | `from domains.comms.services.video.video_service import get_video_conference` |
| L649 | `from domains.comms.services._auto_stubs import NotificationChannel` | `from domains.comms.services.notifications.notification_models import NotificationChannel` |
| L650 | `from domains.comms.services._auto_stubs import NotificationPriority` | `from domains.comms.services.notifications.notification_models import NotificationPriority` |
| L651 | `from domains.comms.services._auto_stubs import get_notification_engine` | `from domains.comms.services.notifications.notification_service import get_notification_engine` |
| L1030-1039 | 10 imports (add_reaction, apply_legal_hold, etc.) | `from domains.comms.services.messaging.chat_service import ...` |
| L1167-1170 | 4 imports (resolve_address, resolve_recipients, etc.) | `from domains.comms.services.email.email_service import ...` |
| L1228 | `from domains.comms.services._auto_stubs import get_chat_service` | `from domains.comms.services.messaging.chat_service import get_chat_service` |
| L1374 | `from domains.comms.services._auto_stubs import get_internal_communication_service` | `from domains.comms.services.internal.internal_service import ...` |
| L1467 | `from domains.comms.services._auto_stubs import handle_message` | `from domains.comms.services.messaging.message_handler import handle_message` |
| L1468 | `from domains.comms.services._auto_stubs import record_product_click` | `from domains.comms.services.analytics.click_tracker import record_product_click` |
| L1531-1536 | 5 imports (create_chat_thread, create_incident_room, etc.) | `from domains.comms.services.messaging.chat_service import ...` |

### 4.2 `finance.py` (1808 lines) — 🔴 103 Undefined References

| Line | Broken Import | Fix |
|---|---|---|
| L20 | `from domains.finance.services._auto_stubs import accounting_controller` | `from domains.finance.services.ledger.accounting_controller import accounting_controller` |
| L22-27 | 6 imports (controller_get_ap_summary, etc.) | `from domains.finance.services.ledger.general_ledger_service import ...` |
| L33 | `from domains.finance.services._auto_stubs import FinancialReportingService` | `from domains.finance.services.reporting.reporting_service import FinancialReportingService` |
| L51 | `from domains.finance.services._auto_stubs import trading_service` | `from domains.finance.services.trading_service import trading_service` |
| L630 | `from modules.admin.routers.auth import get_current_user` | `from domains.security.services.iam.security_dependencies import get_current_user` |
| L1185-1234 | 51 imports from `modules.employee.routers.cash_management_controller` | **FILE DOESN'T EXIST** — move logic to `domains/finance/services/` |
| L1433 | `from domains.finance.services._auto_stubs import FinancialReportingService` | (duplicate) |
| L1435 | `from domains.finance.services._auto_stubs import TreasuryAdapter` | `from domains.finance.services.treasury.treasury_adapter import TreasuryAdapter` |
| L1605 | `from modules.employee.routers.treasury_api import ...` | **FILE DOESN'T EXIST** |
| L1721-1770 | 47 imports from `modules.employee.routers.cash_management_controller` | **DUPLICATE of L1185-1234** |

**Action:** This file is the worst. It needs:
1. Replace all _auto_stubs imports with real domain service imports
2. Delete duplicate blocks (L1185-1234 and L1721-1770 are identical)
3. Replace imports from non-existent controller files with domain service imports
4. Move 14 Pydantic models to schemas

### 4.3 `hr.py` (1195 lines) — ⚠️ 29 Inline Pydantic Models + 6 _auto_stubs

| Issue | Lines | Fix |
|---|---|---|
| 29 Pydantic models inline | L93-306 | Move to `domains/hr/schemas/requests.py` |
| L63-70 | 6 _auto_stubs imports | Replace with real `domains.hr.services.*` imports |

### 4.4 `orders.py` (405 lines) — ⚠️ 1 _auto_stubs + 11 Inline Pydantic

| Issue | Line | Fix |
|---|---|---|
| `trading_service` from _auto_stubs | L51 | `from domains.finance.services.trading_service import trading_service` |
| 11 Pydantic models inline | L57-163 | Move to `domains/finance/schemas/requests.py` |
| Cross-module import | L13 | `from modules.admin.routers.auth import get_current_user` → `from domains.security.services.iam.security_dependencies import get_current_user` |

### 4.5 `suppliers.py` (454 lines) — ⚠️ 5 _auto_stubs

| Line | Broken Import | Fix |
|---|---|---|
| L141 | `from domains.comms.services._auto_stubs import get_video_conference` | `from domains.comms.services.video.video_service import get_video_conference` |
| L219 | (duplicate of L141) | Remove duplicate |
| L358 | `from domains.comms.services._auto_stubs import NotificationChannel` | `from domains.comms.services.notifications.notification_models import NotificationChannel` |
| L359 | `from domains.comms.services._auto_stubs import NotificationPriority` | `from domains.comms.services.notifications.notification_models import NotificationPriority` |
| L360 | `from domains.comms.services._auto_stubs import get_notification_engine` | `from domains.comms.services.notifications.notification_service import get_notification_engine` |
| L451 | `from modules.employee.routers.email_controller import router` | Move email_controller logic to `domains/comms/services/` |

---

## 5. Module: Logistics — Problems & Fixes

### 5.1 `logistics.py` (1984 lines) — ⚠️ 59 Duplicate Routes + 3 Cross-Module

| Issue | Fix |
|---|---|
| 59 duplicate route registrations | Delete lines 1260-1970 (entire duplicate block) |
| L153: `from modules.admin.routers.core_auth_routes import get_current_user` | `from domains.security.services.iam.security_dependencies import get_current_user` |
| L567: `from modules.admin.routers.auth import get_current_user` | Same fix |
| L1271: `from modules.admin.routers.core_auth_routes import get_current_user` | Same fix |
| 8 inline Pydantic models | Move to `domains/logistics/schemas/` |

**Action:** Delete the entire second half of the file (lines ~1260-1970) which is an exact duplicate of lines ~554-962.

---

## 6. Module: Supplier — Problems & Fixes

### 6.1 `finance.py` (239 lines) — ⚠️ 19 Colon-Feature Strings

| Current (Wrong) | Correct |
|---|---|
| `finance:commission:read` | `finance.commission.read` |
| `finance:commission:write` | `finance.commission.write` |
| `finance:ledger:read` | `finance.ledger.read` |
| `finance:payout:read` | `finance.payout.read` |
| `finance:payout:write` | `finance.payout.write` |
| `finance:bank:read` | `finance.bank.read` |
| `finance:bank:write` | `finance.bank.write` |

**Action:** Find-and-replace all colons with dots in `require_feature()` calls.

---

## 7. Implementation Priority

### Week 1: Fix Broken Code

| # | Task | File | Lines |
|---|---|---|---|
| 1 | Add 21 svc_* imports | admin/country.py | L11-17 |
| 2 | Add wishlist imports | admin/customers.py | L14 |
| 3 | Add email_metrics import | admin/orders.py | L17 |
| 4 | Fix 1 _auto_stubs import | customer/comms.py | L15 |
| 5 | Fix 3 undefined refs | customer/finance.py | L261, L351 |
| 6 | Delete 2 duplicate functions | customer/customers.py | L23-41, L57-75 |
| 7 | Delete 11 duplicate routes + move models | customer/promotions.py | L71-256 |
| 8 | Fix 29 _auto_stubs imports | employee/comms.py | L164-1536 |
| 9 | Fix 103 undefined refs | employee/finance.py | L20-1770 |
| 10 | Fix 6 _auto_stubs + move 29 models | employee/hr.py | L63-306 |
| 11 | Fix 1 _auto_stubs + 11 models | employee/orders.py | L51-163 |
| 12 | Fix 5 _auto_stubs | employee/suppliers.py | L141-451 |
| 13 | Delete 59 duplicate routes | logistics/logistics.py | L1260-1970 |
| 14 | Fix 19 colon-feature strings | supplier/finance.py | All `require_feature()` calls |

### Week 2: Cleanup

| # | Task | Files |
|---|---|---|
| 15 | Fix 3 cross-module imports | logistics/logistics.py L153, L567, L1271 |
| 16 | Move 89 Pydantic models to schemas | 6 files |
| 17 | Populate analytics.py | admin/analytics.py |

---

## 8. Summary

| Module | Broken | Cleanup | Total |
|---|---|---|---|
| **Admin** | 24 undefined refs | 9 models + analytics | 33 |
| **Customer** | 4 undefined + 1 _auto_stubs | 11 dupes + 7 models | 23 |
| **Employee** | 47 _auto_stubs + 103 undefined | 60 models + 32 cross-module | 242 |
| **Logistics** | 0 | 59 dupes + 8 models + 3 cross | 70 |
| **Supplier** | 0 | 19 colon + 5 models | 24 |
| **TOTAL** | **179** | **275** | **454** |

**The employee module is 242/454 (53%) of all remaining work.**

---

*Document generated following ARCHITECTURE_DIAGRAM.md rules*  
*All routers have 0 DB calls ✅*  
*Subdirectories deleted ✅*  
*Thin router Law #2 satisfied for DB operations ✅*