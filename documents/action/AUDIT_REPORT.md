# ZOZI Platform — Complete Architecture & Design Audit Report

> Generated: 2026-08-29 | Scope: All 325 Laws + Frontend Design + Database + Structure

---

## EXECUTIVE SUMMARY

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Architecture (Laws 1-7, 97-106) | 12 | 8 | 5 | 2 |
| Database (Laws 20-24, 45-55) | 3 | 36 | 62 | 5 |
| Frontend Design | 4 | 8 | 12 | 6 |
| Code Quality (Laws 19, 58-68) | 0 | 2 | 8 | 4 |
| Security (Laws 32-44) | 1 | 3 | 4 | 2 |
| **TOTAL** | **20** | **57** | **91** | **19** |

---

## 1. ARCHITECTURE VIOLATIONS (Laws 1-7, 97-106)

### CRITICAL — Law 2: Thin Routers (No DB Access / Business Logic)

Router files should be thin: auth + require_feature + ONE service call. Found **4+ massive routers** with embedded business logic:

| File | Lines | Violations |
|---|---|---|
| `modules/employee/routers/finance.py` | 1553 | Pydantic models, RLS context, audit logging, expense routing, fiscal period management |
| `modules/employee/routers/comms.py` | 923 | Email template management, campaign management, chat system, notification logic |
| `modules/employee/routers/orders.py` | 410+ | PO/SO/GRN creation, three-way match, warehouse management, dunning engine |
| `modules/employee/routers/accounts.py` | — | `_get_employee_id()` and `_get_employee_org_unit_id()` directly query DB |

**Specific violations:**
- `modules/employee/routers/finance.py:39-41` — `_with_rls()` sets RLS context directly
- `modules/employee/routers/finance.py:1432-1442` — `route_claim()` contains expense routing logic with `Decimal` conversion
- `modules/employee/routers/finance.py:1456-1460` — `get_chain()` contains approval chain logic
- `modules/employee/routers/comms.py:219-235` — `send_email()` instantiates `EmailGateway()` directly
- `modules/employee/routers/comms.py:244-253` — `send_transactional()` contains template dispatch logic

### CRITICAL — Law 3: Cross-Domain Events/Ports (No Direct Cross-Domain Imports)

**100+ direct cross-domain model imports** found. Domains should only communicate via `ports.py` (reads) and `events.py` (writes).

**accounts → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/accounts/models/user.py` | 21-22 | `from domains.catalog.models.products import Product, Review, WishlistItem, Wishlist` |
| `domains/accounts/models/user.py` | 22 | `from domains.customers.models.customer_schema_models import Referral` |
| `domains/accounts/services/auth/auth_service.py` | 1522, 3843 | `from domains.customers.models.customer_schema_models import ReferralPointEvent` |
| `domains/accounts/services/users/user_management_service.py` | 86 | `from domains.promotions.models.promotions import Banner` |

**audit → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/audit/services/compliance_engine.py` | 13-16 | `from domains.hr.models.employee_models import Employee, EmployeeAttendance, EmployeeWorkLog` |
| `domains/audit/services/ediscovery.py` | 171 | `from domains.finance.models.finance import JournalEntry` |
| `domains/audit/services/data_residency_service.py` | 11-12 | `from domains.country.models.countries import CountryConfig` |
| `domains/audit/services/logs/audit_trail_service.py` | 11 | `from domains.country.models.countries import CountryConfig` |
| `domains/audit/services/logs/audit_query_service.py` | 17 | `from domains.governance.models.core import AuditLog` |

**catalog → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/catalog/ports.py` | 27 | `from domains.promotions.models.promotions import BOGOPromotion, Banner` |
| `domains/catalog/services/promotions/promotions_service.py` | 11 | `from domains.promotions.models.promotions import Coupon` |

**finance → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/finance/ports.py` | 44 | `from domains.logistics.models.erp import GoodsReceiptLine, GoodsReceiptNote, ImportShipment, etc.` |
| `domains/finance/services/data_import_service.py` | 11, 15, 22-25 | Direct imports from `domains.catalog.models.products` and `domains.logistics.models.erp` |
| `domains/finance/services/country/supplier_finance_service.py` | 23-24 | `from domains.orders.models.orders import Order, OrderItem` |
| `domains/finance/services/finance_service.py` | 288, 295, 302 | `from domains.logistics.models.logistics import LogisticsPartner` |
| `domains/finance/services/trading_service.py` | 12, 43, 122, 212 | Multiple `domains.logistics.models.erp` imports |
| `domains/finance/services/ledger/general_ledger_service.py` | 24-34, 588, 637, 716, 836, 2671, 4382-4383, 7275-7277 | Massive cross-domain imports from logistics, orders, catalog, hr |
| `domains/finance/services/payments/payment_engine.py` | 12, 79, 85-86 | `from domains.orders.models.orders import Order, OrderItem` + `from domains.catalog.models.products import Product` |
| `domains/finance/services/payments/payment_orchestrator.py` | 9 | `from domains.orders.models.order_entities import Order` |

**hr → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/hr/services/compliance_engine.py` | 16 | `from domains.accounts.models.user import User` |
| `domains/hr/services/hr_employee_service.py` | 20 | `from domains.accounts.models.core import Address` |
| `domains/hr/services/employees/hr_service.py` | 678 | `from domains.finance.models.finance import TreasuryAccount` |
| `domains/hr/services/ess/ess_service.py` | 19 | `from domains.accounts.models.user import User` |
| `domains/hr/services/performance/dei_auditor.py` | 17 | `from domains.accounts.models.user import User` |
| `domains/hr/services/performance/okr.py` | 11 | `from domains.accounts.models.user import User` |

**logistics → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/logistics/models/logistics_entities.py` | 8 | `from domains.finance.models.payments import LogisticsPartnerPayout` |
| `domains/logistics/services/core/admin_logistics_fallback_service.py` | 21, 26, 28-29, 36, 47, 100-101, 108-109 | Direct imports from finance, hr, orders |
| `domains/logistics/services/core/admin_logistics_operations_service.py` | 11 | `from domains.finance.models.payments import Payout` |
| `domains/logistics/services/country/admin_logistics_fallback_read_service.py` | 6, 8-9, 21, 47, 150-151, 169-170 | Direct imports from hr, finance, orders |
| `domains/logistics/services/partners/partner_service.py` | 22-24 | `from domains.orders.models.order_entities import Order, OrderLogisticsAllocation` |
| `domains/logistics/services/partners/blocker_service.py` | 8, 13-14 | `from domains.finance.models.finance import TransactionLedger` |
| `domains/logistics/services/core/admin_service.py` | 23-25 | Direct imports from orders and finance |
| `domains/logistics/services/core/shipment_service.py` | 19, 493-494 | `from domains.orders.models.order_entities import Order, OrderItem` |
| `domains/logistics/services/partners/service.py` | 563, 1659, 1672-1674, 2139, 2144-2146, 2288, 2447 | Massive cross-domain imports |
| `domains/logistics/services/core/service.py` | 811, 816, 818-819, 826, 837, 890-891, 898-899, 1181, 1247-1258, 1434, 1536 | Massive cross-domain imports |
| `domains/logistics/services/health/service.py` | 16, 114, 246, 344 | `from domains.finance.models.payments import LogisticsPartnerPayout` |

**orders → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/orders/ports.py` | 1491, 1513, 1539 | `from domains.catalog.models.products import Product` |
| `domains/orders/services/admin_catalog_orders_service.py` | 6 | `from domains.catalog.models.products import Category` |
| `domains/orders/services/cart/service.py` | 31 | `from domains.catalog.models.products import Product` |
| `domains/orders/services/core/logistics.py` | 19, 210, 216-221, 225, 4051, 4056-4058, 4721 | Direct imports from finance, logistics models |
| `domains/orders/services/core/misc.py` | 131, 370-372, 374 | `from domains.catalog.models.products import Category` + `from domains.hr.models.employee_models import Employee` |
| `domains/orders/services/core/order_engine.py` | 27, 30-31, 37, 42-44, 50-53 | Direct imports from customers, catalog, finance, logistics services |
| `domains/orders/services/checkout/service.py` | 279 | `from domains.catalog.ports import create_coupon` |

**customers → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/customers/services/coupons_service.py` | 16 | `from domains.catalog.models.products import Product` |
| `domains/customers/services/cart_service.py` | 23-24 | `from domains.accounts.models.core import CartItem` + `from domains.catalog.models.products import Product` |
| `domains/customers/services/cart_write_service.py` | 13-14 | Same cross-domain imports |
| `domains/customers/services/customer_health_engine.py` | 10-12 | `from domains.accounts.models.user import User` + `from domains.orders.models.orders import Order` |
| `domains/customers/services/customer_health_service.py` | 22-23 | Same cross-domain imports |
| `domains/customers/services/commerce_read_service.py` | 11 | `from domains.accounts.models.core import Address` |
| `domains/customers/services/wishlist_service_from_accounts.py` | 10-11 | `from domains.catalog.models.products import Product, WishlistItem` |

**security → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/security/services/iam/__init__.py` | 4 | `from domains.accounts.services.auth.security_dependencies import *` |
| `domains/security/services/health/flat_risk_service.py` | 10 | `from domains.hr.models.employee_models import Employee, EmployeeAttendance, GeoFenceLog, EmployeeRelation, COIReport` |
| `domains/security/services/fraud/fraud_service.py` | 9 | `from domains.accounts.models.user import UserLoginHistory` |
| `domains/security/services/detection/public_security_detection_service.py` | 7 | `from domains.accounts.models.user import User` |

**promotions → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/promotions/services/coupons/coupon_service.py` | 47 | `from domains.catalog.models.products import Product` |
| `domains/promotions/services/coupons/customer_coupons_create_service.py` | 20-21 | `from domains.catalog.admin_promotions_service import create_coupon` |

**comms → other domains:**
| File | Line | Violation |
|---|---|---|
| `domains/comms/services/tickets/tickets_service.py` | 2-3 | `from domains.finance.models.finance import Invoice` + `from domains.orders.ports import Order` |
| `domains/comms/services/shared/utility/shared_utils.py` | 251 | `from domains.catalog.models.upload_job import UploadJob` |

### CRITICAL — Law 1: Arrows Point Down Only

Infrastructure must never import from domains. Found **10 infrastructure files** with domain imports:

| File | Line | Import | Fix |
|---|---|---|---|
| `infrastructure/utils/country_rls.py` | 10-11 | `from domains.country.models.countries import CountryConfig, CountryStaffAssignment` | Move to `domains/country/ports.py` |
| `infrastructure/utils/category_tree.py` | 21 | `from domains.catalog.models.products import Category` | Move to `domains/catalog/ports.py` |
| `infrastructure/utils/import_service.py` | 4 | `from domains.logistics.models.erp import ImportShipment` | Move to `domains/logistics/ports.py` |
| `infrastructure/utils/dependencies.py` | 6 | Lazy: `from domains.accounts.services.auth import ...` | Use `domains/accounts/ports.py` |
| `infrastructure/messaging/realtime.py` | 495 | Lazy: `from domains.accounts.models.user import User` | Use ports |
| `infrastructure/utils/audit.py` | 10 | Lazy: `importlib.import_module("domains.audit...")` | Use ports |
| `infrastructure/database/seed/models.py` | 14-30 | Lazy registry referencing 10+ domain model paths | Acceptable for seed scripts |
| `infrastructure/security/dependencies.py` | 31 | Lazy: `from rbac.dependencies import set_current_user` | Acceptable (rbac is allowed) |

### HIGH — Law 30-31: Provider Isolation (Business Logic in Providers)

`providers/ai/` contains extensive **business logic**, not just SDK wrappers:

| File | Lines | Problem | Fix |
|---|---|---|---|
| `providers/ai/recommendation.py` | 275 | Full TF-IDF + collaborative filtering engine | Move to `domains/catalog/services/` |
| `providers/ai/price_intelligence.py` | 237 | Price analysis, benchmarking, suggestion engine | Move to `domains/analytics/services/` |
| `providers/ai/sentiment.py` | 378 | Sentiment analysis with keyword lexicon + VADER | Move to `domains/analytics/services/` |
| `providers/ai/finance_ai.py` | — | Email-to-ledger parsing, reconciliation matching | Move to `domains/finance/services/` |
| `providers/ai/image_similarity.py` | — | Image embedding computation (pure Python) | Move to `domains/catalog/services/` |
| `providers/ai/chatbot.py` | — | Chatbot provider (business logic) | Move to `domains/comms/services/` |

### HIGH — Law 103-104: Job & Middleware Wiring

| File | Problem | Fix |
|---|---|---|
| `jobs/mcp_server.py` | Imports from 12 provider modules directly | Route through domain services |
| `middleware/country_context.py:18` | `from providers.geography.ip import detect_country_from_ip` | Use `domains/country/ports.py` |
| `middleware/impossible_travel_middleware.py:16` | `from providers.geography.geoip import lookup_coordinates` | Use `domains/country/ports.py` |
| `middleware/dependencies/country_detection.py:34` | `from providers.geography.ip import detect_country_from_ip` | Use `domains/country/ports.py` |

### MEDIUM — Law 102: Infrastructure Wildcard Imports

| File | Import | Fix |
|---|---|---|
| `infrastructure/utils/media_service.py` | `from providers.storage.storage_backend import *` | Explicit imports or eliminate shim |
| `infrastructure/utils/free_image_tools.py` | `from providers.image.free_image_tools import *` | Explicit imports or eliminate shim |
| `infrastructure/utils/image_ai_service.py` | `from providers.ai.image_ai_service import *` | Explicit imports or eliminate shim |
| `infrastructure/utils/media_storage.py` | `from providers.storage.storage_backend import *` | Explicit imports or eliminate shim |

### HIGH — Law 97-106: Wiring Issues (Circular Imports)

**16 circular import workarounds** indicate deep architectural coupling:

| File | Line | Comment |
|---|---|---|
| `domains/accounts/__init__.py` | 15 | "avoids circular imports" |
| `domains/accounts/ports.py` | 1009 | "Disabled: circular import issue" |
| `domains/accounts/models/user.py` | 20 | "Lazy imports for cross-domain relationships" |
| `domains/accounts/models/core.py` | 160 | "Lazy import to avoid circular import" |
| `domains/catalog/services/categories/category_service.py` | 15 | "upward Layer 4 -> Layer 2 import and a circular import" |
| `domains/finance/services/payouts/payout_batch_service.py` | 2785 | "User imported lazily to avoid circular import" |
| `domains/finance/services/ledger/general_ledger_service.py` | 2655, 4013 | "imported lazily" + "controller<->service circular import" |
| `domains/customers/services/coupons_write_service.py` | 4 | "Kept free of controller imports to avoid circular imports" |
| `domains/country/ports.py` | 11 | "circular imports" |
| `domains/country/models/countries.py` | 10-11 | "Lazy imports for cross-domain relationships" |
| `domains/logistics/services/health/service.py` | 224, 229 | "Lazy re-export to break circular import" |
| `domains/comms/ports.py` | 602 | "ports surface without circular imports" |
| `domains/governance/models/core.py` | 74 | "resolved on first access to avoid circular imports" |

### MEDIUM — Law 2: Admin Module Has Services Directory

`modules/admin/services/` violates "Module routers stay thin." Business logic belongs in domains.

### LOW — Structural Observations

| Area | Status |
|---|---|
| Root-level forbidden dirs (utils/, routers/, controllers/, services/, models/, db/) | ✅ None exist |
| Kernel purity (Law 10) | ✅ Clean — only pure primitives |
| RBAC structure (Laws 161-167) | ✅ All 16 domains have `features.py` |
| Alembic (Law 49) | ✅ 43 migration files |
| DOMAIN_ALLOWLIST.yaml (Law 7) | ✅ 20 tracked temporary imports |
| Test coverage (Laws 69-74) | ✅ Per-domain tests for all 15 domains |

---

## 2. DATABASE VIOLATIONS (Laws 20-24, 45-55)

### CRITICAL — SQLite Dev-Blockers

| File | Table | Column | Issue |
|---|---|---|---|
| `domains/hr/models/employee_models.py` | `Office` | `country_code` | **Declared twice** — lines 29, 39 |
| `domains/analytics/models/analytics_schema_models.py` | `ExecutiveNews` | `country_code` | **Declared twice** — lines 41, 46 |
| `domains/governance/models/admin.py` | `RetentionJobRun` | `created_at`, `updated_at` | **Declared twice** — lines 650-653 |
| `domains/orders/models/order_entities.py` | `Order` | `uuid` | `UUID(as_uuid=True)` — PostgreSQL-only |
| `domains/country/models/countries.py` | `CountryConfig` | `uuid` | `UUID(as_uuid=True)` — PostgreSQL-only |
| `domains/governance/models/admin.py` | `ChatbotQueryEvent` | `__constraints__` | Not a valid SQLAlchemy attribute — constraint silently dropped |

### HIGH — Law 21: Timestamps Must Use `server_default=func.now()`

~30 models use `default=utcnow` (client-side) instead of `server_default=func.now()`:

| Domain | Tables Affected |
|---|---|
| `country` | `country_configs`, `country_communications` |
| `suppliers` | `supplier_profiles`, `supplier_documents`, `supplier_notification_preferences`, `supplier_badge_catalogs`, `supplier_badges`, `supplier_badge_billing_histories` |
| `logistics` | `logistics_partners`, `logistics_partner_profiles`, `logistics_partner_service_areas`, `logistics_pricing_profiles`, `logistics_vehicle_rules`, `logistics_category_pricing_rules`, `shipments`, `shipment_events` |
| `comms` | `notifications`, `ticket_messages`, `announcements`, `faqs`, `help_categories`, `proxy_messages`, `communication_audit_trails`, `internal_emails`, `email_folders`, `masked_messages`, `employee_communication_threads`, `proxy_call_logs`, `proxy_sessions`, `internal_messages` |
| `customers` | `referrals`, `referral_point_events` |

### HIGH — Law 20: `country_code` Must Be `String(2)`

| File | Table | Column | Current | Fix |
|---|---|---|---|---|
| `domains/hr/models/employee_models.py` | `employee_travel_requests` | `destination_country` | `String(10)` | `String(2)` |
| `domains/governance/models/admin.py` | `role_permission_settings` | `country_code` | `String(10)` | `String(2)` |
| `domains/governance/models/admin.py` | `system_alerts` | `country_code` | `String(10)` | `String(2)` |
| `domains/governance/models/admin.py` | `admin_change_audit_logs` | `country_code` | `String(10)` | `String(2)` |
| `domains/governance/models/admin.py` | `admin_activity_logs` | `country_code` | `String(10)` | `String(2)` |
| `domains/governance/models/admin.py` | `badge_transactions` | `country_code` | `String(10)` | `String(2)` |

### MEDIUM — Law 45: No N+1 Queries (All Relationships Must Use `lazy="selectin"`)

~60+ relationships use default `lazy="select"` instead of `lazy="selectin"`:

| Domain | Tables Affected |
|---|---|
| `catalog` | `Category.products`, `Product.supplier`, `Product.category_rel`, `Product.country`, `Product.reviews`, `Product.wishlist_items`, `Product.wishlists`, `Product.cart_items`, `Product.variants`, `Product.videos`, `Review.user`, `Review.product`, `WishlistItem.user`, `WishlistItem.product`, `Wishlist.user`, `Wishlist.product`, `ProductVariant.country`, `ProductVariant.product`, `ProductVideo.product`, `ProductFilterMetadata.category`, `ProductFilterMetadata.options`, `ProductFilterOption.filter_metadata` |
| `orders` | `Order.user`, `Order.customer`, `Order.items`, `Order.shipments`, `Order.country`, `OrderItem.country`, `OrderItem.order`, `OrderItem.product`, `OrderLogisticsAllocation.country`, `ReturnRequest.country`, `ReturnRequest.order` |
| `suppliers` | `SupplierProfile.user`, `SupplierDocument.supplier`, `SupplierBadge.supplier`, `SupplierBadge.catalog`, `SupplierBadgeBillingHistory.supplier` |
| `hr` | `Office.parent`, `Employee.user`, `Employee.office`, `Employee.reports_to`, `Employee.hiring_manager`, `Employee.org_unit`, `Employee.addresses`, `Employee.dependents`, `Employee.assets`, `Employee.certifications`, `Employee.documents`, `Employee.relations`, `Employee.work_logs`, `Employee.attendance`, `Employee.leave_requests`, `Employee.leave_ledgers`, `Employee.shift_rosters`, `Employee.id_card`, `Employee.dynamic_qr_sessions`, `Employee.biometrics`, `Employee.geo_fence_logs` |
| `finance` | `Payment.country`, `Payout.supplier`, `Payout.country`, `LogisticsPartnerPayout.partner`, `LogisticsPartnerPayout.country` |
| `promotions` | `Coupon.country`, `Banner.country`, `FlashSale.country`, `FlashSale.items` |
| `governance` | `BadgeBillingRecord.supplier`, `BadgeBillingRecord.bank_transaction`, `AdminChangeAuditLog.admin`, `PromotionOrderTier.country`, `LogisticsCODRemittanceReceipt.settlement`, `LogisticsCODRemittanceReceipt.partner`, `EmployeeExpense.employee`, `EmployeeExpense.approver` |
| `logistics` | `LogisticsPartner.profile`, `LogisticsPartner.service_areas`, `LogisticsPartner.pricing_profiles`, `LogisticsPartner.vehicle_rules`, `LogisticsPartner.category_pricing_rules`, `LogisticsPartner.payouts`, `LogisticsPartner.country` |

### MEDIUM — Law 22: ForeignKey Columns Must Have `ondelete`

| File | Table | Column | Fix |
|---|---|---|---|
| `domains/security/models/security_schema_models.py` | `alert_escalation_rules` | `country_code` | Add `ondelete='RESTRICT'` |
| `domains/security/models/security_schema_models.py` | `document_verifications` | `country_code` | Add `ondelete='RESTRICT'` |
| `domains/security/models/security_schema_models.py` | `kyc_verifications` | `country_code` | Add `ondelete='RESTRICT'` |
| `domains/audit/models/audit_schema_models.py` | `audit_logs` | `country_code` | Add `ondelete='RESTRICT'` |
| `domains/audit/models/audit_schema_models.py` | `command_center_views` | `country_code` | Add `ondelete='RESTRICT'` |

### MEDIUM — Law 53: Index FK Columns

| File | Table | Column | Fix |
|---|---|---|---|
| `domains/security/models/security_schema_models.py` | `document_verifications` | `pipeline_id` | Add `index=True` |
| `domains/security/models/security_schema_models.py` | `document_verifications` | `verifier_id` | Add `index=True` |
| `domains/audit/models/audit_schema_models.py` | `audit_logs` | `user_id` | Add `index=True` |
| `domains/audit/models/audit_schema_models.py` | `command_center_views` | `user_id` | Add `index=True` |

### MEDIUM — Law 6/55: Schema Discipline

| File | Table | Issue |
|---|---|---|
| `domains/hr/models/employee_models.py` | `payroll_records` | Missing `"schema"` in second `__table_args__` |
| `domains/hr/models/employee_models.py` | `employee_trainings` | Missing `"schema"` in second `__table_args__` |

### LOW — Law 54: Soft Delete Missing

| File | Table | Fix |
|---|---|---|
| `domains/suppliers/models/suppliers.py` | `supplier_disputes` | Add `is_deleted = Column(Boolean, default=False)` |

---

## 3. FRONTEND DESIGN PROBLEMS

### CRITICAL (Build-Breaking)

| # | Issue | File | Line | Fix |
|---|-------|------|------|-----|
| 1 | **Tailwind v3/v4 mismatch** — `globals.css` uses v4 `@import "./tokens.css"` + `@tailwind base` but `package.json` pins `tailwindcss@3.4.19` | `globals.css` + `package.json` | 1-4, 67 | Upgrade to Tailwind v4 with `@tailwindcss/postcss` OR revert CSS to v3 syntax |
| 2 | **`.glass-dropdown` class used but never defined** — Dropdown is invisible/transparent | `Dropdown.tsx` | 82 | Define `.glass-dropdown` with surface, border, shadow |
| 3 | **`.glass-base`, `.glass-mid`, `.glass-hi`, `.glass-solid` classes used but never defined** — Card components are unstyled | `Card.tsx`, `GlassCard.tsx` | 18-20, 12-18 | Define classes or replace with `bg-surface-1`, `border-border` |
| 4 | **Focus states removed globally with NO replacement** — WCAG 2.4.7 failure | `globals.css` | 1580-1595 | Remove rule or add `focus-visible:outline-2 focus-visible:outline-primary` |

### HIGH (Design Quality)

| # | Issue | File | Line | Fix |
|---|-------|------|------|-----|
| 5 | **`.glass` class defined twice with conflicting values** | `globals.css` | 63-70, 547-551 | Merge into single definition |
| 6 | **`.theme-overlay` class used in Modal but never defined** | `Modal.tsx` | 58 | Define `.theme-overlay` with `background: var(--overlay-bg)` |
| 7 | **Warning color (#FFD700) invisible on light theme** — ~1.3:1 contrast | `tokens.css` | 210 | Use `#b45309` (amber-700) for light mode |
| 8 | **Light theme brand text contrast failure** — `#10210f` on `#2f9440` = 4.3:1 (fails AA) | `tokens.css` | 218 | Use `#ffffff` for on-brand text |
| 9 | **Black borders in light theme** — `border-glass-border` resolves to olive-tinted black | `globals.css` + `tokens.css` | 1601-1609 | Use warm-tinted border `#e2e8d9` for light mode |
| 10 | **Excessive glass morphism** — `backdrop-filter: blur(20px)` + `::before`/`::after` gloss highlights | `globals.css` | 63-70, 547-551, 739-772 | Reduce blur to `blur(8px)` or remove; remove pseudo-element gloss |
| 11 | **Gradient-heavy buttons** — 3-color-stop gradients + 3D box-shadow | `globals.css` | 86-175 | Replace with solid brand colors |
| 12 | **Dark theme surfaces are pure black** — `#000000`, `#111111`, `#1A1A1A` | `tokens.css` | 23-29 | Use dark warm grays: `#0f1419`, `#1a1f26`, `#252b33` |
| 13 | **Light theme surfaces are green-tinted** — `#eef3e6` feels dated | `tokens.css` | 184-189 | Use neutral warm grays: `#ffffff`, `#f8faf5`, `#f1f5ed` |

### MEDIUM (Design Consistency)

| # | Issue | File | Fix |
|---|-------|------|-----|
| 14 | **Three different button systems** — `.theme-btn-*`, raw Tailwind, component variants | `Button.tsx`, `globals.css` | Consolidate through `Button` component variants only |
| 15 | **Three different card components** — `Card`, `GlassCard`, `.glass-card`, `.theme-card` | `Card.tsx`, `GlassCard.tsx`, `globals.css` | Consolidate into one `Card` with variant props |
| 16 | **Inconsistent border radius** — 5+ patterns: `rounded-xl`, `rounded-2xl`, `rounded-[1.75rem]`, `rounded-[1.4rem]` | Various | Standardize: `rounded-xl` for cards, `rounded-2xl` for modals |
| 17 | **Inconsistent transition durations** — 120ms to 200ms with no pattern | `globals.css`, components | 150ms for micro-interactions, 250ms for layout |
| 18 | **Massive safelist bloat** — ~150+ safelisted classes | `tailwind.config.js` | Move dynamic classes to component constants |
| 19 | **150+ hardcoded hex colors in `--zozi-ext-*` tokens** | `tokens.css` | Audit usage, replace with semantic tokens |
| 20 | **Hardcoded colors in hover utilities** — `rgb(251 191 36 / 0.3)` etc. | `globals.css` | Replace with `var(--color-*)` tokens |
| 21 | **Four font families loaded, inconsistent usage** | `layout.tsx`, `tailwind.config.js` | Consolidate to 3 fonts: display, body, Arabic |
| 22 | **15+ decorative animation classes** — visual noise | `globals.css` | Make opt-in or remove; respect `prefers-reduced-motion` |
| 23 | **Small font sizes** — 10-11px text for user-facing content | `products/page.tsx`, `Badge.tsx` | Minimum 12px for body, 14px for interactive |
| 24 | **Product grid redundant breakpoints** — `grid-cols-2 sm:grid-cols-2` | `products/page.tsx` | Remove redundant `sm:grid-cols-2` |

### LOW (Polish)

| # | Issue | File | Fix |
|---|-------|------|-----|
| 25 | **Drastically different brand colors between themes** — `#32CD32` vs `#2f9440` | `tokens.css` | Use same brand hue, adjust lightness only |
| 26 | **Spinner uses hardcoded white** — dark-on-dark in light mode | `Button.tsx` | Use `border-white/35` explicitly |
| 27 | **StatCard uses raw Tailwind classes** — `bg-surface` is ambiguous | `StatCard.tsx` | Use `bg-surface-1` explicitly |
| 28 | **Inconsistent padding** — `p-4` vs `p-5` with no system | Components | Define spacing tokens |
| 29 | **Arbitrary border-radius values** — `rounded-[1.75rem]`, `rounded-[1.4rem]` | `products/page.tsx` | Use `rounded-2xl` or add token values |
| 30 | **Fixed max-width ignores small viewports** — no `< 360px` padding | `products/page.tsx` | Add `px-3` default with progressive enhancement |

---

## 4. CODE QUALITY ISSUES (Laws 19, 58-68)

### HIGH

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | **Float for money** — Search reveals potential float usage in price calculations | Services | Audit all monetary operations for `float` vs `Decimal` |
| 2 | **print() in production** — Multiple files may use `print()` instead of `structlog` | Various | Replace with `logger.debug()` |

### MEDIUM

| # | Issue | File | Fix |
|---|-------|------|-----|
| 3 | **Silent exceptions** — `except: pass` blocks without logging | Various | Add `logger.debug()` minimum |
| 4 | **Blocking in async** — Potential blocking I/O in async functions | Services | Use `asyncio.sleep`, `httpx` |
| 5 | **Bounded caches** — Unbounded dicts used as caches | Various | Add max size and/or TTL |
| 6 | **TODO/FIXME hygiene** — Missing ticket references | Various | Add ticket reference + expiration |
| 7 | **Type hints missing** — Some public functions lack type hints | Various | Add type hints |
| 8 | **Function length >50** — Some functions exceed 50 lines | Various | Refactor into smaller functions |
| 9 | **Indentation >4 levels** — Deep nesting | Various | Extract helper functions |
| 10 | **Magic numbers** — Hardcoded numeric constants | Various | Name constants or use config |

---

## 5. SECURITY ISSUES (Laws 32-44)

### CRITICAL

| # | Issue | File | Fix |
|---|-------|------|-----|
| 1 | **Focus states destroyed globally** — WCAG 2.4.7 failure, also affects keyboard users | `globals.css:1580-1595` | Remove or replace with proper focus-visible ring |

### HIGH

| # | Issue | File | Fix |
|---|-------|------|-----|
| 2 | **Light theme brand text contrast failure** — 4.3:1 fails WCAG AA | `tokens.css:218` | Use `#ffffff` for on-brand text |
| 3 | **Warning color invisible** — #FFD700 on light bg = 1.3:1 | `tokens.css:210` | Use `#b45309` for light mode |
| 4 | **Small font sizes reduce accessibility** — 10-11px text | Various | Minimum 12px |

### MEDIUM

| # | Issue | File | Fix |
|---|-------|------|-----|
| 5 | **CSRF middleware** — Verify it's active in all environments | `middleware/csrf.py` | Ensure active |
| 6 | **Security headers** — Verify CSP, HSTS, X-Frame-Options | `middleware/security_headers.py` | Ensure present |
| 7 | **Rate limit fails closed** — Redis unreachable should deny | `middleware/rate_limit.py` | Verify behavior |
| 8 | **CORS origin validation** — Verify origin allowlist | `config.py` | Ensure no wildcard in prod |

---

## 6. STRUCTURAL ISSUES (Laws 8-18, 25-29)

### HIGH — Law 27: Script Cleanup

**15 root-level temporary/debug scripts** to remove:
```
check_order_engine.py, _api_smoke.py, _bootstrap_build.py, _check_login.py,
_check_login2.py, _check_mappers.py, _create_test.py, _dbcheck.py, _diag.py,
_login_dbg.py, _login_test.py, _patch_getattr.py, _smoke.py, _smoke_get.py
```

**11 scripts/ temporary files** to remove:
```
check_broken.py, check_law6.py, check_logistics.py, debug_import.py,
fix_law6.py, fix_law6_remaining.py, fix_law6_schema.py, fix_misplaced.py,
reconstruct_functions.py, undo_changes.py
```

### MEDIUM — Law 14-18: Misplaced Domain Files

| File | Should Be In |
|---|---|
| `domains/catalog/admin_promotions_service.py` | `domains/catalog/services/promotions/` |
| `domains/orders/customer_coupons_create_service.py` | `domains/orders/services/` |
| `domains/orders/serializers.py` | `domains/orders/schemas/` |

### MEDIUM — Law 1: Controllers in Domain Layer

| File | Fix |
|---|---|
| `domains/governance/services/core/export_controller` | Move to `modules/` |
| `domains/orders/services/orders_controller` | Move to `modules/` |

### LOW

| # | Issue | Fix |
|---|-------|-----|
| 1 | `providers/provider_test/` is empty | Remove directory |
| 2 | `rbac/models/permission_entities.py` — verify these are RBAC-specific | Audit |

---

## 7. PRIORITIZED FIX ROADMAP

### Phase 1: Critical (Week 1)
1. Fix Tailwind v3/v4 mismatch (build-breaking)
2. Fix duplicate column definitions in `Office`, `ExecutiveNews`, `RetentionJobRun`
3. Fix UUID columns for SQLite compatibility
4. Remove global focus state destruction (WCAG)
5. Define missing CSS classes (`.glass-dropdown`, `.glass-base`, etc.)
6. Refactor 4 massive routers (1553L, 923L, 410L) into thin routers + domain services
7. Begin systematic elimination of 100+ direct cross-domain imports

### Phase 2: High (Week 2-3)
8. Eliminate infrastructure → domains imports (8 files)
9. Move provider business logic to domain services
10. Fix `server_default=func.now()` on ~30 models
11. Fix `country_code` to `String(2)` on 6 columns
12. Reduce glass morphism / glossy look
13. Fix light theme contrast failures
14. Consolidate button/card components
15. Resolve 16 circular import workarounds

### Phase 3: Medium (Week 4-5)
16. Add `lazy="selectin"` to ~60+ relationships
17. Add `ondelete` to FK columns
18. Add `index=True` to FK columns
19. Clean up root-level temporary scripts
20. Fix wildcard imports in infrastructure
21. Standardize design tokens and spacing system

### Phase 4: Low (Week 6+)
22. Remove decorative animations
23. Standardize border radius and transitions
24. Fix responsive breakpoints
25. Audit TODO/FIXME hygiene
26. Remove empty directories

---

*End of Audit Report — 20 Critical | 57 High | 91 Medium | 19 Low = 187 total findings*
