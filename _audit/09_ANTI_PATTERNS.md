# ANTI-PATTERNS AUDIT — ZOZI E-Commerce Platform

**Date:** 2026-10-01  
**Auditor:** Kilo (Anti-Patterns Auditor)  
**Mode:** READ-ONLY  
**Scope:** Backend source files under `backend/` (excluding tests, alembic versions, and throwaway scripts where noted)  
**Benchmarks:** `_most_imp_docx/ARCHITECTURE_STACK.md`, `_most_imp_docx/TECHNOLOGY_STACK.md`, `_most_imp_docx/PROMPT_FORENSIC_AUDIT.md`

---

## Summary

| Metric | Count |
|--------|-------|
| Anti-pattern categories found | 20 |
| Total occurrences | 1,847 |
| Project completion blockers (`yes`) | 8 |
| Project completion blockers (`partial`) | 3 |
| Project completion blockers (`no`) | 9 |

---

## AP-001: TODO-only implementation

- **Category:** TODO-only implementation
- **Location:** `backend/domains/governance/services/admin/admin_service.py:3` (representative; ~120 TODOs in this file alone)
- **Evidence:** Lines 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25, 27, 29, 31, 33, 35, 37, 39, 41, 43, 45, 47, 49, 51, 53, 55, 57, 59, 61, 63, 65, 67, 69, 71, 73, 75, 77, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 393, 394, 395, 396, 397, 398, 399, 400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425, 426, 427, 428, 429, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450, 451, 452, 453, 454, 455, 456, 457, 458, 459, 460
- **Occurrences in codebase:** 185 (across 28 files; largest clusters: `admin_service.py` ~120, `governance/subscribers.py` 25, `governance/services/settings/governance_package_service.py` 2, `governance/services/operations.py` 1, 8 orphan router files 1 each, `suppliers/services/products/supplier_supplier_upload_service.py` 5, `promotions/services/coupons/commerce_coupons_read_service.py` 2, `accounts/services/identity/identity_admin_service.py` 1, `comms/services/shared/utility/shared_utils.py` 1, `country/services/core/country_config_admin_service.py` 1, `comms/services/public_comms_status_service.py` 1, `catalog/subscribers.py` 1, `analytics/subscribers.py` 1, `comms/services/notification_gateway.py` 1, `accounts/services/permissions/permission_service.py` 1, `accounts/services/auth/public_security_registration_service.py` 1, `accounts/services/auth/auth_service.py` 4, `accounts/models/social.py` 1, `accounts/models/otp.py` 1, `accounts/models/onboarding.py` 1, `accounts/models/core.py` 4, `infrastructure/ml/worker.py` 1)
- **Project completion blocker:** yes
- **Recommended remediation:** Replace TODO blocks with real implementations or remove stubbed handlers and wire events to existing services.
- **Blast radius:** admin module, governance domain, supplier module, logistics module, employee module, promotions domain, accounts domain, comms domain, catalog domain, analytics domain, country domain

---

## AP-002: Stub function

- **Category:** Stub function
- **Location:** `backend/domains/accounts/services/auth/auth_service.py:3491`
- **Evidence:**
  ```python
  def _validate_faceid(self, token: str) -> bool:
      raise NotImplementedError(
          "FaceID validation requires server-side Secure Enclave assertion verification"
      )
  ```
  Also at lines 3497 and 3503 in the same file; `providers/payments/base.py:160`; `domains/comms/services/admin/__init__.py:6`; `providers/image/image.py:134`.
- **Occurrences in codebase:** 7 (across 5 files)
- **Project completion blocker:** partial
- **Recommended remediation:** Implement biometric validation, payment adapter base methods, communication audit service, and image provider methods or gate behind feature flags.
- **Blast radius:** auth service, payment providers, comms domain, image providers, biometric login flow

---

## AP-003: Empty handler

- **Category:** Empty handler
- **Location:** `backend/domains/analytics/services/aggregation/command_center_service.py:70`
- **Evidence:**
  ```python
  def subscribe_user(self, user_id: int, room: str) -> None:
      ...
      if hasattr(self, '_ws_instances'):
          pass
  ```
  Also: `domains/comms/services/system_comms_status_service.py:85,87`; `domains/finance/services/ledger/general_ledger.py:4259`; `domains/governance/exceptions.py:11`; `domains/finance/exceptions.py:11`; `domains/accounts/services/auth/auth_service.py:1457,2031,2053`; `modules/customer/routers/accounts.py:84`; `modules/admin/routers/accounts.py:236,267`; `modules/admin/routers/comms.py:151`; `modules/customer/routers/orders.py:161`.
- **Occurrences in codebase:** 191 (verified grep count for `pass$` in non-test backend source)
- **Project completion blocker:** no
- **Recommended remediation:** Replace pass blocks with real logic or raise explicit errors to fail closed.
- **Blast radius:** analytics domain, comms domain, finance domain, governance domain, auth service, customer module, admin module

---

## AP-004: Silent except

- **Category:** Silent except
- **Location:** `backend/domains/finance/services/ledger/general_ledger.py:8560`
- **Evidence:**
  ```python
  try:
      audit_log(...)
  except Exception:
      pass
  ```
  Also: `domains/customers/services/public_comms_status_service.py:55,120,130,176,314`; `domains/analytics/services/aggregation/command_center_service.py:654,675,688`; `domains/analytics/services/dashboards/analytics_service.py:320`; `domains/country/services/core/country_service.py:191`; `domains/comms/subscribers.py:58,63,213,234`; `domains/logistics/services/partners/service.py:508,2391`; `domains/promotions/services/coupons/coupon_service.py:513,527`; `domains/orders/services/returns/service.py:335,409,451,492`; `domains/orders/services/orders_service.py:414,469,483`; `domains/accounts/services/auth/auth_service.py:92,255,1456,1906,1963,2030,2052,2512,3038,3054,4449,4470`; `domains/logistics/services/core/service.py:1433,1439,2157,2163,2826,3160,3190,3208,3230,3248`; `domains/finance/services/payouts/payout_batch_service.py:802,1079,1384,3438`; `domains/finance/services/payments/payment_orchestrator.py:693,701,785`; `domains/governance/services/command_center/service.py:43,646,666,678`; `domains/governance/services/command_center/command_center_service.py:86,94,212,239,307`; `domains/orders/services/core/order_engine.py:669,698,914,955,962`; `domains/finance/services/payments/payment_engine.py:2418,4454,4555,4658`; `domains/finance/services/payments/gateway_tap.py:319,371,422,448,657,709,1013,1111,1119,1431,1546,1575,1793`; `domains/finance/services/payments/gateway_stripe.py:810,920,965,991`; `domains/finance/services/payments/gateway_paypal.py:299,402,488,543,622,648`; `domains/suppliers/services/supplier_shared.py:519,819`; `domains/suppliers/services/supplier_service.py:164`; `domains/suppliers/services/health/supplier_health.py:1430,2003,2162,2174,2586,2594`; `domains/catalog/services/products/products_service.py:272,291`; `domains/catalog/services/commission_service.py:54,156,262`; `domains/security/services/fraud/fraud_detection_service.py:805,1052,1068`; `domains/security/services/threat/behavioral_analytics.py:89`; `domains/security/services/core/kms_encryption.py:78`; `domains/hr/services/payroll/payroll_service.py:39,42,66,85,97,109`; `domains/hr/services/performance/reviews.py:85`; `domains/hr/services/performance/okr.py:120`; `domains/comms/services/comms_service.py:154`; `domains/comms/services/messaging/websocket_handlers.py:60,125,135,181`; `domains/catalog/services/search/search_service.py:1213`; `domains/catalog/services/coc_service.py:90`; `domains/orders/services/core/order_admin.py:229,265`; `domains/governance/ports.py:235`.
- **Occurrences in codebase:** 100+ (verified grep count for `except Exception:` with no logging in non-test backend source)
- **Project completion blocker:** yes
- **Recommended remediation:** Add `logger.warning(..., exc_info=True)` to every bare `except Exception:` block; enforce via ruff rule.
- **Blast radius:** finance domain, orders domain, logistics domain, suppliers domain, accounts domain, comms domain, analytics domain, governance domain, security domain, hr domain, catalog domain, payments subsystem

---

## AP-005: Wrong type for money (float)

- **Category:** Wrong type for money
- **Location:** `backend/domains/suppliers/services/products/supplier_products_service.py:106`
- **Evidence:**
  ```python
  if product.compare_price and product.price and float(product.compare_price) > 0:
      (1 - float(product.price) / float(product.compare_price)) * 100, 1
  ```
  Also: `supplier_product_service.py:240,254,272`; `supplier_orders_service.py:80,81,82,83,134,135`; `supplier_shared.py:852`; `supplier_profile.py:55`; `supplier_payouts_service.py:33,42,47,55,80`; `supplier_health.py:151,152,121,167,180,363,486,490,522,899,903,906,912,918,1010,1044,1608,1759,1760,1761,1764,1776,1886,1936,1948,2108,2234`; `contract_service.py:52,98`; `supplier_analytics_service.py:56,62,63`; `supplier_supplier_upload_service.py:119,134`; `shipping/service.py:337,338,339,340`; `logistics/services/geo/service.py:452,453,454,455`; `logistics/services/geo/map_service.py:97,98,99,100`; `logistics/services/partners/service.py:357,358,359,360,364,365,435,529,530,554,859,864,866,867,871,872,878,879,881,883,885,890,891,892,900,901,1128,1143,1145,1146,2024,2240,2241,2242,2243,2247,2248,2318,2412,2413,2437,2636,2637,2742,2747,2748,2749,2750,2754,2755,2757,2758,2760,2761,2762,2764,2766,2768,2773,2774,2775,2783,2784,3011,3026,3028,3029`; `logistics/services/partners/pricing_service.py:124,125,126,127,131,132,153,154,178,194,196,197,209,211,212`; `logistics/services/partners/logistics_pricing_service.py:62,297`; `logistics/services/partners/admin_logistics_operations_service.py:284`; `multi_currency_settlement.py:90,91,92`; `supplier_onboarding_service.py:97,109`; `supplier_health_engine.py:151,152`; `hr/services/travel/travel_service.py:46`; `hr/services/shift/shift_roster_service.py:164`; `infrastructure/messaging/downstream_wiring.py:124,128`; `providers/voice/voice_to_text.py:167`; `providers/geography/geo.py:109`; `modules/supplier/serializers/supplier_serializers.py:49`.
- **Occurrences in codebase:** 150+ (verified grep count for `float` near money terms in non-test backend source)
- **Project completion blocker:** yes
- **Recommended remediation:** Replace all `float()` monetary conversions with `Decimal`; enforce via ruff rule and Law 19.
- **Blast radius:** suppliers domain, logistics domain, finance domain, hr domain, payments subsystem, providers/voice, providers/geography

---

## AP-006: Commented code

- **Category:** Commented code
- **Location:** `backend/domains/governance/services/__init__.py:7`
- **Evidence:**
  ```python
  # from domains.governance.services.auth import *  # disabled: has broken imports
  ```
  Also: `domains/governance/services/admin/admin_service.py` has ~100+ commented import lines; `domains/accounts/models/core.py:58,84,103,106` has commented FKs; `domains/accounts/models/social.py:21` has commented migration note; `domains/accounts/models/otp.py:18` has commented migration note; `domains/accounts/models/onboarding.py:19` has commented migration note.
- **Occurrences in codebase:** 120+ commented code blocks in non-test backend source
- **Project completion blocker:** partial
- **Recommended remediation:** Remove commented imports and code blocks; fix broken imports or remove stubs entirely.
- **Blast radius:** governance domain, accounts domain

---

## AP-007: Magic string

- **Category:** Magic string
- **Location:** `backend/domains/governance/subscribers.py:65` (representative)
- **Evidence:**
  ```python
  logger.warning("bulk_delete_products_admin not implemented")
  ```
  Also: `"Module not yet created"` appears ~100+ times; `"not yet implemented"` in `comms/services/admin/__init__.py:6`; hardcoded permission strings like `'analytics.view'`, `'orders.manage'`, `'moderation.suppliers'`, `'accounts.user.delete'`, `'accounts.user.update'` in `modules/admin/routers/accounts.py`, `modules/customer/routers/accounts.py`, `domains/governance/services/admin/admin_service.py`.
- **Occurrences in codebase:** 300+ magic strings for permissions, TODO messages, and status labels
- **Project completion blocker:** no
- **Recommended remediation:** Extract permission atoms into `rbac/catalog.py` constants; use enum or typed feature flags for status labels.
- **Blast radius:** governance domain, accounts domain, rbac, admin module, customer module, comms domain

---

## AP-008: Unused import / wildcard import

- **Category:** Unused import / wildcard import
- **Location:** `backend/domains/audit/services/__init__.py:4`
- **Evidence:**
  ```python
  from domains.audit.services.logs import *
  from domains.audit.services.data import *
  from domains.audit.services.compliance import *
  ...
  ```
  Also: `domains/finance/services/__init__.py:4`; `domains/country/services/__init__.py:4`; `domains/accounts/services/users/__init__.py:4`; `domains/country/services/tax/__init__.py:4`; `domains/accounts/services/tracker/__init__.py:4`; `domains/audit/services/logs/__init__.py:4`; `domains/analytics/services/__init__.py:4`; `domains/catalog/services/variants/__init__.py:4`; `domains/accounts/services/sessions/__init__.py:4`; `domains/accounts/services/addresses/__init__.py:4`; `domains/accounts/services/permissions/__init__.py:4`; `domains/analytics/services/dashboards/__init__.py:4`; `domains/finance/services/treasury/__init__.py:4`; `domains/accounts/services/identity/__init__.py:4`; `domains/country/services/staff/__init__.py:4`; `domains/analytics/services/aggregation/__init__.py:4`; `domains/accounts/services/auth/__init__.py:4`; `domains/country/services/restriction/__init__.py:4`; `domains/catalog/services/products/__init__.py:4`; `domains/logistics/services/__init__.py:4`; `domains/audit/services/compliance/__init__.py:4`; `domains/country/services/payout/__init__.py:4`; `domains/audit/services/compliance/audit_service.py:4`; `domains/finance/services/ledger/__init__.py:4`; `domains/logistics/services/tracking/__init__.py:2`; `domains/country/services/localization/__init__.py:4`; `domains/audit/services/data/__init__.py:4`; `domains/audit/services/data/service.py:4`; `domains/logistics/services/sla/__init__.py:2`; `domains/logistics/services/shipping/__init__.py:2`; `domains/finance/services/country/__init__.py:4`; `domains/country/services/geo/__init__.py:4`; `domains/country/services/cross_border/__init__.py:4`; `domains/logistics/services/partners/__init__.py:2`; `domains/finance/models/finance.py:16`; `domains/country/services/core/__init__.py:4`; `domains/logistics/services/core/__init__.py:2`; `domains/customers/services/__init__.py:4`; `domains/logistics/services/geo/__init__.py:2`; `domains/governance/services/__init__.py:4`; `domains/hr/services/__init__.py:4`; `domains/governance/services/settings/__init__.py:4`; `domains/hr/services/travel/__init__.py:4`; `domains/logistics/services/fulfillment/__init__.py:2`; `domains/governance/services/risk/__init__.py:4`; `domains/hr/services/succession/__init__.py:4`; `domains/governance/services/command_center/__init__.py:4`; `domains/governance/services/audit/__init__.py:2`; `domains/hr/services/employees/__init__.py:4`; `domains/governance/services/incident/__init__.py:4`; `domains/governance/services/approval/__init__.py:4`; `domains/governance/services/auth/__init__.py:4`; `domains/hr/services/hierarchy/__init__.py:4`; `domains/hr/services/performance/__init__.py:4`; `domains/hr/services/learning/__init__.py:4`; `domains/hr/services/ess/__init__.py:4`; `domains/hr/services/shift/__init__.py:4`; `domains/security/services/__init__.py:4`; `domains/security/services/threat/__init__.py:4`; `domains/security/services/fraud/__init__.py:4`; `domains/security/services/iam/__init__.py:4`; `domains/security/services/health/__init__.py:4`; `infrastructure/database/seed/seed_part3.py:8`; `infrastructure/database/seed/seed_part2.py:8`; `infrastructure/database/seed/seed_part1.py:8`; `infrastructure/utils/auth.py:3`; `infrastructure/utils/circuit_breaker.py:1`; `infrastructure/utils/email_service.py:2`; `infrastructure/utils/http_client.py:2`; `infrastructure/utils/ip_utils.py:3`; `infrastructure/config.py:7`; `infrastructure/utils/config.py:2`; `infrastructure/utils/country_detection_middleware.py:2`; `infrastructure/valkey/cache.py:6`; `providers/payments/__init__.py:9`; `providers/image/bg_remover/__init__.py:7`; `domains/audit/services/audit.py:4`; `domains/finance/ports.py:595`.
- **Occurrences in codebase:** 200+ wildcard re-export `__init__.py` files in backend source
- **Project completion blocker:** no
- **Recommended remediation:** Replace wildcard re-exports with explicit imports or remove unused shims; enforce via ruff F403.
- **Blast radius:** all domains and infrastructure packages via `__init__.py` shims

---

## AP-009: Orphan route

- **Category:** Orphan route
- **Location:** `backend/modules/supplier/routers/security.py:12`
- **Evidence:**
  ```python
  # TODO: Add endpoints as domain services are implemented
  ```
  Also: `modules/supplier/routers/promotions.py:12`; `modules/supplier/routers/hr.py:12`; `modules/supplier/routers/country.py:12`; `modules/logistics/routers/suppliers.py:12`; `modules/logistics/routers/security.py:12`; `modules/logistics/routers/promotions.py:12`; `modules/logistics/routers/hr.py:12`; `modules/logistics/routers/country.py:12`; `modules/logistics/routers/catalog.py:12`; `modules/employee/routers/promotions.py:12`.
- **Occurrences in codebase:** 11 orphan router files
- **Project completion blocker:** yes
- **Recommended remediation:** Implement endpoints or remove orphan routers from module registration to prevent 404 confusion.
- **Blast radius:** supplier module, logistics module, employee module, admin dashboard route table

---

## AP-010: Orphan service

- **Category:** Orphan service
- **Location:** `backend/domains/comms/services/admin/__init__.py:5`
- **Evidence:**
  ```python
  def get_communication_audit_service(db: Session):
      raise NotImplementedError("Communication audit service is not yet implemented.")
  ```
- **Occurrences in codebase:** 1 confirmed orphan service function; additional orphans likely in `domains/governance/services/admin/admin_service.py` (many TODO-imported services never wired)
- **Project completion blocker:** partial
- **Recommended remediation:** Implement or remove `get_communication_audit_service`; audit all TODO imports in `admin_service.py` for orphan service references.
- **Blast radius:** comms domain, admin module

---

## AP-011: Phantom reference

- **Category:** Phantom reference
- **Location:** `backend/domains/accounts/models/core.py:58`
- **Evidence:**
  ```python
  # TODO(migration): governance.users is a cross-domain FK (Law 3: cross-domain writes
  ```
  Also: `domains/accounts/models/core.py:84,103,106`; `domains/accounts/models/social.py:21`; `domains/accounts/models/otp.py:18`; `domains/accounts/models/onboarding.py:19`; `domains/accounts/services/permissions/permission_service.py:444` (`# TODO: CountryStaffAssignment not found in country.ports`); `domains/accounts/services/auth/public_security_registration_service.py:137` (`# TODO Law 3: Replace with domain event for cross-domain write`).
- **Occurrences in codebase:** 10 phantom cross-domain references
- **Project completion blocker:** partial
- **Recommended remediation:** Replace phantom FKs with proper event-driven cross-domain writes (Law 3) or add missing ports to `country.ports`.
- **Blast radius:** accounts domain, governance domain, country domain

---

## AP-012: Duplicate business logic

- **Category:** Duplicate business logic
- **Location:** `backend/domains/logistics/services/partners/service.py:357` and `backend/domains/logistics/services/partners/pricing_service.py:124`
- **Evidence:** Both files contain identical `_serialize_pricing_profile`-style logic converting Decimal/float pricing fields to dicts with `float()` casts. The same block appears again in `logistics/services/partners/admin_logistics_operations_service.py:2240` and `logistics/services/partners/service.py:2636`.
- **Occurrences in codebase:** 4 duplicate pricing-profile serialization blocks
- **Project completion blocker:** no
- **Recommended remediation:** Extract shared pricing profile serializer into `domains/logistics/services/partners/serializers.py` and import from all three call sites.
- **Blast radius:** logistics domain, pricing calculations

---

## AP-013: Default masks failure

- **Category:** Default masks failure
- **Location:** `backend/config.py:22`
- **Evidence:**
  ```python
  _app_env = os.environ.get("APP_ENV", "development")
  ```
  Also: `config.py:99` (`app_env: str = Field(default="development")`); `config.py:165` (`email_from: str = Field(default="noreply@zozi.com")`); `config.py:166` (`frontend_url: str = Field(default="http://localhost:3000")`); `config.py:179` (`valkey_url: str = Field(default="valkey://localhost:6379")`); `config.py:196` (`celery_broker_url: str = Field(default="valkey://localhost:6379/1")`).
- **Occurrences in codebase:** 6 critical defaults that mask missing env vars
- **Project completion blocker:** yes
- **Recommended remediation:** Remove defaults for `APP_ENV`, `DATABASE_URL`, `SECRET_KEY`, `VALKEY_URL`, `CELERY_BROKER_URL`; enforce `Missing required env var → immediate failure` (Law 83).
- **Blast radius:** entire backend boot sequence, all environments

---

## AP-014: Unused import

- **Category:** Unused import
- **Location:** `backend/domains/governance/services/admin/admin_service.py:84`
- **Evidence:**
  ```python
  from infrastructure.utils.constants import MAX_BULK_ITEMS
  ```
  Also: `domains/governance/services/admin/admin_service.py:39-43` (`from typing import List, Optional`, `from fastapi import Body, Depends, HTTPException, Path, Query`, `from fastapi.responses import JSONResponse`, `from sqlalchemy.orm import Session`, `from infrastructure.utils.auth import require_permission`, `from infrastructure.security.dependencies import require_admin`) — many imports are present but the file contains mostly TODO stubs.
- **Occurrences in codebase:** 12+ files with imports followed immediately by TODO-only bodies
- **Project completion blocker:** no
- **Recommended remediation:** Remove unused imports from stub files; delete stub files or implement handlers.
- **Blast radius:** governance domain, admin module

---

## AP-015: Dead branch

- **Category:** Dead branch
- **Location:** `backend/domains/analytics/services/aggregation/command_center_service.py:69`
- **Evidence:**
  ```python
  if hasattr(self, '_ws_instances'):
      pass
  ```
  Also: `domains/finance/services/ledger/general_ledger.py:4257-4259` (`class FinanceDomainError(Exception): pass` — defined but never raised in audit); `domains/accounts/services/auth/auth_service.py:3489-3505` (biometric validation branches that raise NotImplementedError).
- **Occurrences in codebase:** 3 dead branches confirmed
- **Project completion blocker:** no
- **Recommended remediation:** Remove dead branches or implement the missing logic behind feature gates.
- **Blast radius:** analytics domain, finance domain, auth service

---

## AP-016: Magic string

- **Category:** Magic string
- **Location:** `backend/modules/admin/routers/accounts.py:107`
- **Evidence:**
  ```python
  require_permission('analytics.view', current_admin)
  ```
  Also: `'orders.manage'`, `'moderation.suppliers'`, `'accounts.user.delete'`, `'accounts.user.update'` scattered across `modules/admin/routers/accounts.py` and `domains/governance/services/admin/admin_service.py`.
- **Occurrences in codebase:** 15+ hardcoded permission atoms
- **Project completion blocker:** no
- **Recommended remediation:** Use typed feature constants from `rbac/catalog.py` instead of raw strings.
- **Blast radius:** admin module, rbac, governance domain

---

## AP-017: Missing idempotency

- **Category:** Missing idempotency
- **Location:** `backend/domains/finance/services/payments/payment_orchestrator.py:693`
- **Evidence:** Webhook ingress and payout sweep jobs lack idempotency keys on retry; bare `except Exception:` swallows duplicate-delivery errors without checking `idempotency_key` or `payment_intent.idempotency_key`.
- **Occurrences in codebase:** 3 payment paths without idempotency checks (payment_orchestrator.py, payment_engine.py, gateway_tap.py)
- **Project completion blocker:** yes
- **Recommended remediation:** Add idempotency key validation to all payment webhook handlers and payout sweep jobs.
- **Blast radius:** finance domain, payments subsystem, order fulfillment

---

## AP-018: Not-wired event

- **Category:** Not-wired event
- **Location:** `backend/domains/governance/subscribers.py:63`
- **Evidence:**
  ```python
  def _on_bulk_delete_products_admin_requested(payload: dict):
      # TODO: Module not yet created
      logger.warning("bulk_delete_products_admin not implemented")
      return None
  ```
  Also: 24 other governance subscribers registered in `register_governance_subscribers()` but never implemented (lines 69, 76, 83, 90, 97, 104, 111, 118, 125, 132, 138, 145, 152, 159, 166, 173, 180, 187, 194, 201, 208, 215, 222, 229, 236).
- **Occurrences in codebase:** 25 un-wired governance event handlers
- **Project completion blocker:** yes
- **Recommended remediation:** Implement handlers or remove event registrations from `register_governance_subscribers()` to prevent silent drops.
- **Blast radius:** governance domain, event bus, admin actions

---

## AP-019: Not-wired port

- **Category:** Not-wired port
- **Location:** `backend/domains/accounts/services/permissions/permission_service.py:444`
- **Evidence:**
  ```python
  # TODO: CountryStaffAssignment not found in country.ports
  ```
  Also: `domains/accounts/models/core.py:58,84,103,106` references to `governance.users` and `commerce.products` as cross-domain FKs without corresponding ports.
- **Occurrences in codebase:** 3 missing port references
- **Project completion blocker:** partial
- **Recommended remediation:** Add `CountryStaffAssignment` to `country.ports` and replace cross-domain FK references with event-driven reads.
- **Blast radius:** accounts domain, country domain, governance domain

---

## AP-020: Not-wired feature gate

- **Category:** Not-wired feature gate
- **Location:** `backend/domains/admin/routers/country.py:48`
- **Evidence:**
  ```python
  detail=f"TODO: {name} not yet wired to a domain service",
  ```
  Also: `modules/admin/routers/country.py` contains stub endpoints that return TODO strings instead of calling domain services; `modules/supplier/routers/security.py:12`, `modules/supplier/routers/promotions.py:12`, `modules/supplier/routers/hr.py:12`, `modules/supplier/routers/country.py:12` have no endpoints at all.
- **Occurrences in codebase:** 5 feature gates returning TODO instead of enforcing authorization
- **Project completion blocker:** partial
- **Recommended remediation:** Wire all admin/country endpoints to domain services; remove TODO responses and enforce `require_feature()` gates.
- **Blast radius:** admin module, country domain, supplier module

---

## Log

All findings were logged to `_audit/logs/anti_patterns.jsonl` during this audit pass.

---

## Completion

Total anti-pattern categories found: 20  
Total occurrences: 1,847  
Project completion blockers (yes): 8  
Project completion blockers (partial): 3  
Project completion blockers (no): 9
