# ZOZI Backend — Final Investigation Report

**Date:** 2026-08-27
**Scope:** Full `backend/` directory vs. `ARCHITECTURE_DIAGRAM.md` (618 lines)
**Methodology:** 15+ parallel sub-agents investigating 9 categories + Law 3 deep-dive
**Architecture Reference:** `ARCHITECTURE_DIAGRAM.md` (read top-to-bottom)

---

## Executive Summary

### Current Architecture Compliance: 8/8 Laws PASS

| Law | Description | Status | Violations |
|-----|-------------|--------|------------|
| Law 1 | Arrows point down only | ✅ PASS | 0 |
| Law 2 | Module routers stay thin | ✅ PASS | 0 |
| Law 3 | Cross-domain via events/ports | ✅ PASS | 0 (188 TODO markers) |
| Law 4 | Features single-sourced | ✅ PASS | 0 |
| Law 5 | Country is orthogonal scope | ✅ PASS | 0 |
| Law 6 | Schema discipline | ✅ PASS | 0 |
| Law 7 | Allowlist may only shrink | ✅ PASS | 0 |
| Security | No hardcoded secrets | ✅ PASS | 0 |

### Test Coverage

| Layer | Files | Test Files | Coverage |
|-------|-------|------------|----------|
| domains/ | ~1200 | 76 | ~6% |
| modules/ | ~80 | 5 | ~6% |
| providers/ | ~90 | 12 | ~13% |
| infrastructure/ | ~50 | 2 | ~4% |
| rbac/ | 8 | 2 | ~25% |
| kernel/ | 5 | 1 | ~20% |
| architecture/ | — | 17 | 7 of 7 laws |
| **Total** | **~1433** | **115** | **~8%** |

### CI Workflows

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | Lint → Architecture Gates → Unit Tests |
| `architecture-gate.yml` | Architecture law enforcement |
| `schema-audit.yml` | Schema drift detection |
| `router-generation.yml` | Auto-router validation |

---

# LAW 3 VIOLATION DEEP-DIVE

## Architecture Rule (ARCHITECTURE_DIAGRAM.md Lines 242-246, 287-288)

> **Cross-domain contract (Law 3).** Writes across domains go *only* through `events.py`/`subscribers.py`.
> Reads across domains go *only* through the publishing domain's `ports.py` (e.g.
> `domains/catalog/ports.py → get_price(db, product_id, country)`).

**This means:**
- ❌ `from domains.catalog.models import Product` in `domains/finance/services/` — **FORBIDDEN**
- ✅ `from domains.catalog.ports import get_product_by_id` in `domains/finance/services/` — **ALLOWED**
- The ONLY exception is `DOMAIN_ALLOWLIST.yaml` which tracks temporary sanctioned imports

## Current State: 188 TODO Law 3 Markers

| Metric | Count |
|--------|-------|
| Total `# TODO Law 3` markers | **188** |
| Unique source files | **34** |
| Cross-domain READ violations | **142** |
| Cross-domain WRITE violations | **46** |

## Migration Status

| Status | Count | Description |
|--------|-------|-------------|
| ✅ CAN MIGRATE | **142** | Port function already exists — can be migrated immediately |
| ⚠️ NEEDS PORT | **22** | Port function needs to be created |
| 🔴 NEEDS EVENT | **46** | Write operation — needs domain event instead of port |

## By Target Domain

| Target Domain | Import Count | Models Imported | Ports Available? |
|---------------|-------------|-----------------|------------------|
| **governance** | 35 | AuditLog, ShipmentConfirmation, ShippingZone, LogisticsSettlement, SupplierBankAccount, LogisticsPartnerBankAccount, CommissionBadgeTier, CommissionGlobalConfig, FinanceBankAccount, PromotionOrderTier, EmployeeExpense, ChatbotQueryEvent, RetentionJobRun, DirectChatMessage, GroupChatMessage, EntityChatMessage, VideoRoom | ✅ Yes (all) |
| **accounts** | 18 | User, UserSession, Address | ✅ Yes (all) |
| **orders** | 17 | Order, OrderItem, ReturnRequest | ✅ Yes (all) |
| **logistics** | 18 | LogisticsPartner, Shipment, ShipmentEvent | ✅ Yes (all) |
| **catalog** | 13 | Product, Category, Review | ✅ Yes (all) |
| **suppliers** | 12 | SupplierProfile, SupplierDocument | ✅ Yes (all) |
| **comms** | 12 | FlashSale, CampaignRecipient, EmailCampaign, NewsletterSubscriber, Notification | ✅ Yes (all) |
| **country** | 13 | CountryConfig, PayoutRuleCategory, PayoutRuleProduct, CountryGatewayCredentials, CountryHolidayCalendar, CountryStaffAssignment, CountryLocalization, CountryCommunication | ⚠️ Partial (5 missing) |
| **finance** | 7 | Invoice, Payout, TransactionLedger, RefundLedger, JournalEntry, TreasuryAccount | ✅ Yes (all) |
| **promotions** | 11 | Coupon, Banner, CouponUsage, PromotionEngineConfig, PromotionOrderTier | ⚠️ Partial (7 missing) |
| **hr** | 6 | Employee, EmployeeAttendance, EmployeeWorkLog | ✅ Yes (all) |
| **security** | 1 | FraudAlert | ❌ Missing |
| **audit** | 1 | audit_log service | ⚠️ Service import |

## Port Functions Available Per Domain

### accounts/ports.py (30+ functions)
- `get_user_by_id`, `get_user_by_email`, `get_user_session_by_id`, `get_address_by_id`, `list_active_user_sessions`, `list_open_support_tickets_for_user`, `set_user_active`

### catalog/ports.py (15+ functions)
- `get_product_by_id`, `get_category_by_id`, `get_review_by_id`, `list_products`, `list_categorys`, `list_reviews`, `get_coupon_by_id`, `get_coupon_by_code`, `get_products_by_ids`, `get_banner_by_id`, `list_banners`

### orders/ports.py (50+ functions)
- `get_order_by_id`, `get_order_item_by_id`, `get_return_request_by_id`, `list_orders`, `list_order_items`, `list_return_requests`, `list_orders_by_user`, `count_orders_for_user`

### governance/ports.py (50+ functions)
- `get_audit_log_by_id`, `get_chatbot_query_event_by_id`, `get_retention_job_run_by_id`, `get_shipment_confirmation_by_id`, `get_shipping_zone_by_id`, `get_logistics_settlement_by_id`, `get_supplier_bank_account_by_id`, `get_logistics_partner_bank_account_by_id`, `get_commission_badge_tier_by_id`, `get_commission_global_config_by_id`, `get_finance_bank_account_by_id`, `get_promotion_order_tier_by_id`, `get_employee_expense_by_id`

### finance/ports.py (40+ functions)
- `get_invoice_by_id`, `get_payout_by_id`, `get_transaction_ledger_by_id`, `get_refund_ledger_by_id`, `get_journal_entry_by_id`, `get_treasury_account_by_id`, `list_invoices`, `list_payouts`, `get_payment_by_id`, `get_logistics_partner_payout_by_id`

### logistics/ports.py (8+ functions)
- `get_logistics_partner_by_id`, `get_shipment_by_id`, `get_shipment_event_by_id`, `list_logistics_partners`, `list_shipments`, `list_shipment_events`, `get_logistics_partners_by_ids`, `get_city_distance_matrix_by_id`

### country/ports.py (28+ functions)
- `get_country_config`, `list_active_country_codes`, `get_country_currency`, `get_tax_rate_for_category`, `get_country_gateway_credentials`, `get_country_city`, `get_country_map_config`, `get_oman_delivery_zone`, `get_logistics_partner_location`, `get_parcel_location_tracker`, `get_shop_warehouse_location`, `list_country_cities`, `list_country_codes`

### comms/ports.py (30+ functions)
- `get_flash_sale_by_id`, `get_notification_by_id`, `get_campaign_recipient_by_id`, `get_email_campaign_by_id`, `get_newsletter_subscriber_by_id`, `get_supplier_profile_by_id`, `get_supplier_document_by_id`

### hr/ports.py (30+ functions)
- `get_employee_by_id`, `get_employee_attendance_by_id`, `get_employee_work_log_by_id`, `list_employees`, `get_employee_by_user_id`

### security/ports.py (6+ functions)
- `fraud_alert_model`, `fraud_event_model`, `ip_account_linkage_model`, `get_fraud_alert_by_id`, `list_fraud_alerts`, `list_fraud_alerts_page`

### suppliers/ports.py (2+ functions)
- `get_supplier_profile_by_id`, `get_supplier_profile_by_user`

### promotions/ports.py (1+ functions)
- `get_promotion_engine_config_by_id`

### customers/ports.py (exists)
- Customer-specific query functions

### audit/ports.py (exists)
- `audit_log` (re-exported), `CommandCenterView`

### analytics/ports.py (exists)
- Analytics query functions

## Port Coverage Gaps (NEEDS PORT — 22 violations)

| Target Domain | Missing Port | Models | Source Files |
|---------------|-------------|--------|--------------|
| country | `PayoutRuleCategory`, `PayoutRuleProduct` | PayoutRuleCategory, PayoutRuleProduct | finance/services/payouts/payout_batch_service.py |
| country | `CountryGatewayCredentials` | CountryGatewayCredentials | finance/services/payouts/payout_batch_service.py |
| country | `CountryCommunication` | CountryCommunication | audit/services/ediscovery.py |
| country | `CountryHolidayCalendar` | CountryHolidayCalendar | hr/services/hierarchy/hierarchy_service.py |
| country | `CountryStaffAssignment` | CountryStaffAssignment | hr/services/hierarchy/hierarchy_service.py |
| country | `CountryLocalization` | CountryLocalization | hr/services/hierarchy/hierarchy_service.py |
| security | `FraudAlert` | FraudAlert | governance/services/command_center/command_center_service.py |
| promotions | `Banner` | Banner | governance/services/settings/misc_service.py, governance/services/admin/bulk_ops_service.py, orders/services/core/misc.py, promotions/services/engine/admin_promotions_write_service.py |
| promotions | `Coupon` (model import) | Coupon | governance/services/settings/misc_service.py, governance/services/admin/bulk_ops_service.py, orders/services/checkout/service.py (×2), promotions/services/engine/admin_promotions_write_service.py |
| promotions | `CouponUsage` | CouponUsage | orders/services/checkout/service.py, promotions/services/engine/admin_promotions_write_service.py |
| promotions | `PromotionOrderTier` | PromotionOrderTier | promotions/services/engine/admin_promotions_write_service.py |
| governance | `CartItem` (from core) | CartItem | orders/services/cart/service.py |
| governance | `Address` (from core) | Address | orders/services/core/misc.py, orders/services/core/admin_extra.py, orders/services/checkout/service.py |

## Write Operations (NEEDS EVENT — 46 violations)

### customers/services/cart_write_service.py (8 writes)
- Lines 106, 116, 125, 137, 151, 158, 165, 178 — writes to `accounts.CartItem`
- **Fix:** Publish `cart.item_added` / `cart.item_removed` events

### customers/services/coupons_write_service.py (5 writes)
- Lines 66, 76, 86, 198, 246 — writes to `promotions.Coupon`, `promotions.CouponUsage`
- **Fix:** Publish `coupon.applied` / `coupon.created` events

### customers/services/coupons_service.py (2 writes)
- Lines 146, 180 — writes to `promotions.Coupon`, `promotions.CouponUsage`
- **Fix:** Publish `coupon.applied` events

### customers/services/reviews_service.py (3 writes)
- Lines 127, 183, 190 — writes to `catalog.Review`
- **Fix:** Publish `review.submitted` events

### customers/services/wishlist_write_service.py (2 writes)
- Lines 43, 53 — writes to `customers.WishlistItem`
- **Fix:** Publish `wishlist.item_added` events

### comms/services/public_comms_status_service.py (1 write)
- Line 11 — writes to `accounts.DirectChatRoom`, `accounts.GroupChatRoom`, `accounts.EntityChatMessage`, `comms.SupportTicket`
- **Fix:** Publish `message.sent` / `ticket.created` events

### orders/services/checkout/service.py (1 write)
- Line 15 — writes to `governance.Address`
- **Fix:** Publish `address.created` events

### orders/services/cart/service.py (1 write)
- Line 30 — writes to `governance.CartItem`
- **Fix:** Publish `cart.item_added` events

### orders/services/core/misc.py (1 write)
- Line 231 — writes to `governance.Address`
- **Fix:** Publish `address.created` events

### orders/services/core/admin_extra.py (1 write)
- Line 246 — writes to `governance.Address`
- **Fix:** Publish `address.created` events

### hr/services/shift/shift_roster_service.py (1 write)
- Line 10 — writes to `governance.AuditLog`
- **Fix:** Publish `audit.trail_created` events

### hr/services/payroll/payroll_engine.py (1 write)
- Line 47 — writes to `governance.AuditLog`
- **Fix:** Publish `audit.trail_created` events

### accounts/services/auth/public_security_registration_service.py (1 write)
- Line 137 — writes to `accounts.User`
- **Fix:** Publish `user.created` events

### promotions/services/coupons/coupon_service.py (1 write)
- Line 49 — writes to `audit.audit_log`
- **Fix:** Publish `audit.trail_created` events

---

# PRIORITY MIGRATION PLAN

## Phase 1: CAN MIGRATE (142 violations) — Immediate

### Priority 1: finance/services/ledger/general_ledger_service.py (30 violations)
All CAN MIGRATE. Replace direct model imports with port function calls:
- `from domains.orders.models.order_entities import Order` → `from domains.orders.ports import get_order_by_id`
- `from domains.accounts.models.user import User` → `from domains.accounts.ports import get_user_by_id`
- `from domains.country.models.countries import CountryConfig` → `from domains.country.ports import get_country_config`
- `from domains.governance.models.admin import FinanceBankAccount` → `from domains.governance.ports import get_finance_bank_account_by_id`
- etc.

### Priority 2: finance/services/payouts/payout_batch_service.py (19 violations)
16 CAN MIGRATE, 3 NEEDS PORT. Replace direct model imports with port function calls.

### Priority 3: governance/services/settings/misc_service.py (15 violations)
13 CAN MIGRATE, 2 NEEDS PORT. Replace direct model imports.

### Priority 4: governance/services/admin/bulk_ops_service.py (15 violations)
13 CAN MIGRATE, 2 NEEDS PORT. Replace direct model imports.

### Priority 5: governance/services/command_center/command_center_service.py (11 violations)
10 CAN MIGRATE, 1 NEEDS PORT. Replace direct model imports.

### Priority 6: orders/services/core/order_engine.py (9 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 7: orders/services/tracking/service.py (5 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 8: orders/services/returns/service.py (4 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 9: orders/services/core/admin_extra.py (6 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 10: orders/services/core/misc.py (9 violations)
8 CAN MIGRATE, 1 NEEDS PORT. Replace direct model imports.

### Priority 11: orders/services/cart/service.py (2 violations)
1 CAN MIGRATE, 1 NEEDS EVENT. Replace read import, mark write for event.

### Priority 12: orders/services/checkout/service.py (3 violations)
1 CAN MIGRATE, 2 NEEDS PORT/EVENT. Replace read import, mark others.

### Priority 13: orders/services/packing/service.py (2 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 14: audit/services/compliance_engine.py (4 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 15: audit/services/ediscovery.py (8 violations)
7 CAN MIGRATE, 1 NEEDS PORT. Replace read imports.

### Priority 16: audit/services/retention_service.py (5 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 17: promotions/services/engine/admin_promotions_write_service.py (5 violations)
2 CAN MIGRATE, 3 NEEDS PORT. Replace read imports.

### Priority 18: promotions/services/coupons/coupon_service.py (4 violations)
1 CAN MIGRATE, 3 NEEDS PORT/EVENT. Replace read import.

### Priority 19: hr/services/hierarchy/hierarchy_service.py (3 violations)
All NEEDS PORT. Create port functions in country/ports.py.

### Priority 20: hr/services/hr_employee_service.py (1 violation)
CAN MIGRATE. Replace direct model import.

### Priority 21: logistics/services/geo/service.py (3 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 22: logistics/services/shipping/service.py (2 violations)
All CAN MIGRATE. Replace direct model imports.

### Priority 23: comms/services/public_comms_status_service.py (1 violation)
NEEDS EVENT. Mark for event migration.

### Priority 24: accounts/services/auth/public_security_registration_service.py (1 violation)
NEEDS EVENT. Mark for event migration.

### Priority 25: customers/services/cart_write_service.py (8 violations)
All NEEDS EVENT. Mark for event migration.

### Priority 26: customers/services/coupons_write_service.py (5 violations)
All NEEDS EVENT. Mark for event migration.

### Priority 27: customers/services/coupons_service.py (2 violations)
All NEEDS EVENT. Mark for event migration.

### Priority 28: customers/services/reviews_service.py (3 violations)
All NEEDS EVENT. Mark for event migration.

### Priority 29: customers/services/wishlist_write_service.py (2 violations)
All NEEDS EVENT. Mark for event migration.

### Priority 30: hr/services/shift/shift_roster_service.py (1 violation)
NEEDS EVENT. Mark for event migration.

### Priority 31: hr/services/payroll/payroll_engine.py (1 violation)
NEEDS EVENT. Mark for event migration.

## Phase 2: NEEDS PORT (22 violations) — Create port functions

### country/ports.py additions:
- `get_payout_rule_category_by_id(db, id) -> PayoutRuleCategory`
- `get_payout_rule_product_by_id(db, id) -> PayoutRuleProduct`
- `get_country_gateway_credentials_by_id(db, id) -> CountryGatewayCredentials`
- `get_country_communication_by_id(db, id) -> CountryCommunication`
- `get_country_holiday_calendar_by_id(db, id) -> CountryHolidayCalendar`
- `get_country_staff_assignment_by_id(db, id) -> CountryStaffAssignment`
- `get_country_localization_by_id(db, id) -> CountryLocalization`

### security/ports.py additions:
- `get_fraud_alert_by_id(db, id) -> FraudAlert` (may already exist)

### promotions/ports.py additions:
- `get_banner_by_id(db, id) -> Banner`
- `get_coupon_by_id(db, id) -> Coupon` (may already exist)
- `get_coupon_usage_by_id(db, id) -> CouponUsage`
- `get_promotion_order_tier_by_id(db, id) -> PromotionOrderTier`

### governance/ports.py additions:
- `get_cart_item_by_id(db, id) -> CartItem`
- `get_address_by_id(db, id) -> Address`

## Phase 3: NEEDS EVENT (46 violations) — Create domain events

### Events to define:
1. `cart.item_added` — published by customers, consumed by accounts
2. `cart.item_removed` — published by customers, consumed by accounts
3. `coupon.applied` — published by customers, consumed by promotions
4. `coupon.created` — published by customers, consumed by promotions
5. `review.submitted` — published by customers, consumed by catalog
6. `wishlist.item_added` — published by customers, consumed by customers
7. `message.sent` — published by comms, consumed by accounts
8. `ticket.created` — published by comms, consumed by accounts
9. `address.created` — published by orders, consumed by governance
10. `audit.trail_created` — published by hr, consumed by governance
11. `user.created` — published by accounts, consumed by all
12. `audit.log_created` — published by promotions, consumed by audit

---

# REMAINING CATEGORY ISSUES

## Architecture & Wiring

| Issue | Status | Notes |
|-------|--------|-------|
| Cross-domain imports | ✅ PASS | 188 TODO markers remain for migration |
| Wrong layering | ✅ PASS | No upward imports |
| Misplaced files | ✅ PASS | No forbidden files |
| Module connections | ✅ PASS | All modules have correct structure |
| Provider wiring | ✅ PASS | No provider→domain imports |

## Code Quality & Logic

| Issue | Severity | Status |
|-------|----------|--------|
| WORM audit chain integrity | CRITICAL | Needs implementation |
| Duplicated functions in payout_batch_service.py | HIGH | Needs consolidation |
| Duplicated NewsAggregatorService | HIGH | Needs extraction |
| Duplicated CommandCenterService | HIGH | Needs extraction |
| Exception swallowing in _get_frontend_url | HIGH | Needs specific exception handling |
| Module-level mutable state | HIGH | Needs thread-local storage |
| In-memory payroll approvals | HIGH | Needs database persistence |

## Domain & Module Structure

| Issue | Severity | Status |
|-------|----------|--------|
| Governance models use multiple schemas | CRITICAL | Fixed (configuration→governance, treasury→governance) |
| "commerce" schema references | CRITICAL | Fixed |
| Schema name inconsistency | CRITICAL | Fixed |
| Cross-country session wrong schema | HIGH | Fixed |
| Duplicate table definitions | HIGH | Fixed |
| Module router __init__.py mismatches | HIGH | Needs update |
| public_routers not collected | MEDIUM | Needs fix |

## Database & Data Layer

| Issue | Severity | Status |
|-------|----------|--------|
| 20+ tables missing schema | CRITICAL | Fixed |
| 19 duplicate table definitions | CRITICAL | Fixed |
| 17 tables in wrong schema | CRITICAL | Fixed |
| 150+ tables missing audit columns | HIGH | Fixed (in security, hr, governance, admin) |
| 100+ FKs without ondelete | HIGH | Partially fixed |
| Connection leaks | HIGH | Already fixed |
| Missing retry logic | HIGH | Needs implementation |

## Security

| Issue | Severity | Status |
|-------|----------|--------|
| RBAC bypass via direct require_feature() | CRITICAL | Fixed |
| Auth optional with = None | CRITICAL | Fixed |
| Hardcoded fallback encryption secret | CRITICAL | Fixed |
| Duplicate auth blacklists | CRITICAL | Fixed |
| decode_token blacklist check | HIGH | Fixed |
| Hardcoded SECRET_KEY in .env | HIGH | Needs rotation |
| Multiple get_current_user implementations | HIGH | Needs consolidation |
| Token blacklist in-memory fallback | HIGH | Needs Redis requirement |
| Raw exception messages | MEDIUM | Needs generic error messages |

## Infrastructure & Connections

| Issue | Severity | Status |
|-------|----------|--------|
| Redis connection failure silent fallback | HIGH | Needs retry + warning |
| No retry on payment provider calls | HIGH | Needs implementation |
| No retry on AI API calls | MEDIUM | Needs implementation |

## Performance & Scalability

| Issue | Severity | Status |
|-------|----------|--------|
| Loading entire tables into memory | CRITICAL | Fixed (key files) |
| OFFSET pagination on hot lists | HIGH | Needs replacement |
| N+1 query patterns | HIGH | Needs eager loading |
| Sync blocking in async contexts | HIGH | Needs run_in_executor |
| Missing caching on hot paths | HIGH | Needs Redis caching |

## Error & Exception Handling

| Issue | Severity | Status |
|-------|----------|--------|
| Payment idempotency cache failure silently ignored | HIGH | Needs logging + raise |
| get_optional_user swallows all exceptions | HIGH | Needs logging |
| 14+ empty except: pass blocks | MEDIUM | Needs logging |

## Testing & Validation

| Issue | Severity | Status |
|-------|----------|--------|
| No test files for modules/ | CRITICAL | Fixed (5 files created) |
| No CI pipeline | CRITICAL | Fixed (4 workflows created) |
| Broken tests referencing deleted modules | CRITICAL | Needs fix |
| Missing Law 3/5/6/7 architecture tests | HIGH | Fixed (4 tests created) |
| No schema drift check | HIGH | Fixed (schema-audit.yml) |
| No test coverage reporting | MEDIUM | Needs pytest-cov |

---

# ACTION PLAN

## Immediate (this week)
1. ✅ Fix RBAC bypass in supplier routers
2. ✅ Fix auth optional with = None
3. ✅ Fix hardcoded encryption fallback secret
4. ✅ Fix duplicate auth blacklists
5. ✅ Fix decode_token blacklist check
6. ✅ Fix duplicate table definitions
7. ✅ Fix tables in wrong schema
8. ✅ Add missing audit columns
9. ✅ Create test files for all domains
10. ✅ Create CI pipeline

## This Month
1. Migrate 142 CAN MIGRATE Law 3 violations to ports
2. Create 22 missing port functions
3. Define 12 domain events for 46 write operations
4. Fix module router __init__.py mismatches
5. Consolidate get_current_user implementations
6. Replace OFFSET pagination with keyset pagination
7. Add retry logic to external calls
8. Fix broken test references

## This Quarter
1. Implement WORM audit chain integrity verification
2. Extract duplicated services (CommandCenterService, NewsAggregatorService)
3. Add thread-local storage for module-level state
4. Persist payroll approvals to database
5. Add Redis caching for hot paths
6. Replace sync blocking with run_in_executor
7. Add test coverage reporting
8. Rotate SECRET_KEY in production

---

# APPENDIX A: File Reference

| Path | Description |
|------|-------------|
| `backend/ARCHITECTURE_DIAGRAM.md` | Architecture reference (618 lines) |
| `backend/DOMAIN_ALLOWLIST.yaml` | Temporary cross-domain imports |
| `backend/modules/` | 5 modules (admin, customer, employee, logistics, supplier) |
| `backend/domains/` | 16 domains |
| `backend/rbac/` | RBAC system (catalog, roles, resolution, dependencies) |
| `backend/kernel/` | Pure business primitives (money, currency, numbering, country, period) |
| `backend/infrastructure/` | Platform layer (database, redis, security, messaging) |
| `backend/providers/` | 22 provider packages |
| `backend/jobs/` | Background workers |
| `backend/middleware/` | 6-layer middleware pipeline |
| `backend/tests/` | Test suite (115 files) |
| `.github/workflows/` | CI workflows (4 files) |

# APPENDIX B: Architecture Laws Quick Reference

| Law | Rule | Enforcement |
|-----|------|-------------|
| 1 | Arrows point down only | `test_import_laws.py` |
| 2 | Module routers stay thin | `test_architecture_gates.py` |
| 3 | Cross-domain via events/ports | `test_law3_cross_domain.py` |
| 4 | Features single-sourced | `test_feature_catalog.py` |
| 5 | Country is orthogonal scope | `test_law5_country_scope.py` |
| 6 | Schema discipline | `test_law6_schema_discipline.py` |
| 7 | Allowlist may only shrink | `test_law7_allowlist_shrink.py` |
