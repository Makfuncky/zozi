# High Severity Architecture Fixes

**Date:** 2026-08-26
**Agent:** Architecture Fix Agent

---

## Issue 1: Money as float (6 instances fixed)

### Files Modified

#### `domains/finance/services/payments/payment_engine.py`
- Changed `TapChargeRequest.amount` from `Optional[float]` to `Optional[Decimal]`
- Changed `PayTabsChargeRequest.amount` from `Optional[float]` to `Optional[Decimal]`
- Changed `PaymentGatewayConnectionResponse` fields from `float` to `Decimal`:
  - `fee_percent`
  - `fixed_fee_amount`
  - `payout_fee_percent`
  - `payout_fixed_fee_amount`
- Changed `PaymentFinanceQuoteResponse` fields from `float` to `Decimal`:
  - `order_total`
  - `gateway_fee_amount`
  - `customer_payable_total`
  - `processor_net_capture`
  - `taxable_product_amount`
  - `zozi_commission_amount`
  - `supplier_payout_estimate`
  - `logistics_payout_estimate`
  - `estimated_payout_cost`
  - `platform_net_after_gateway_and_payout_costs`
- Replaced `_float_money()` helper with `_round_money_value()` using `Decimal`
- Added `round_money` to kernel.money imports
- Updated all response construction to use `round_money()` instead of `float()`
- Updated defaults dictionary to use `_decimal_from_value()` instead of `float()`

#### `domains/promotions/services/coupons/coupon_service.py`
- Changed `validate_coupon_code()` return values from `float()` to `round_money()`:
  - `discount_amount`
  - `new_total`

#### `domains/orders/services/core/order_engine.py`
- Changed `preview_order()` return values from `float()` to `round_money()`:
  - `subtotal_amount`
  - `discount_amount`
  - `tax_amount`
  - `vat_amount`
  - `shipping_amount`
  - `total_amount`
  - `payment_gateway_fee_amount`
  - `payment_customer_total_amount`
  - `tax_rate`, `tax_amount`, `vat_amount` in `tax_breakdown`
- Changed fraud scoring threshold comparison from `float(total_amount) > 500` to `total_amount > Decimal("500")`
- Changed shipment_quotes `shipping_amount` values from `float()` to `round_money()`
- Changed pricing_breakdown values from `float()`/`0.0` to `round_money()`/`Decimal("0")`
- Changed `tier_discount` in audit log from `float()` to `round_money()`
- Changed order item `total` from `float()` to `round_money()`

---

## Issue 2: Hardcoded secrets (0 instances in production code)

### Finding
No hardcoded secrets were found in production code. All API keys, passwords, and tokens are properly sourced from `settings.*` via environment variables.

The only hardcoded "secrets" found are in test files (e.g., `tests/providers/test_payments_providers.py`, `tests/domains/test_security.py`), which is acceptable test practice.

---

## Issue 3: Duplicate logic (2 pairs addressed)

### Files Deleted

#### `domains/orders/services/core/order_bulk.py`
- Pure placeholder pointing to `bulk.py`
- Only content: `# Bulk order operations are in the existing bulk.py module.`

#### `domains/orders/services/core/order_dtos.py`
- Pure placeholder pointing to `dtos.py`
- Only content: `# DTOs are imported from infrastructure.database.schemas`

### Files Modified

#### `domains/orders/services/core/__init__.py`
- Removed imports from `order_bulk` and `order_dtos`

---

## Issue 4: Missing `__init__.py` exports (13 domains fixed)

### Domains Updated

1. **finance** - Added exports for payments, treasury, payouts, ledger, data_import, country
2. **finance/treasury** - Added exports for treasury_service, cash_management_service
3. **finance/payouts** - Added exports for payout_batch_service
4. **finance/ledger** - Added exports for general_ledger_service
5. **finance/country** - Created new `__init__.py` with exports
6. **promotions** - Added exports for coupons
7. **promotions/coupons** - Added exports for coupon_service and related modules
8. **catalog** - Added exports for products, search, categories, inventory, brands
9. **analytics** - Added exports for dashboards, aggregation, reporting, and services
10. **analytics/dashboards** - Added exports for analytics and admin services
11. **analytics/aggregation** - Added exports for command center services
12. **accounts** - Added exports for auth, users, sessions, permissions, identity, addresses, tracker
13. **accounts/auth** - Added exports for auth_service
14. **accounts/users** - Added exports for users_admin_service
15. **accounts/sessions** - Added exports for session_service
16. **accounts/permissions** - Added exports for permission_service
17. **accounts/identity** - Added exports for identity_admin_service
18. **accounts/addresses** - Added exports for addresses_service
19. **accounts/tracker** - Added exports for live_session_tracker
20. **country** - Added exports for core, geo, cross_border, staff, tax, localization, payout, restriction, research
21. **country/core** - Created new `__init__.py` with exports
22. **country/geo** - Created new `__init__.py` with exports
23. **country/cross_border** - Created new `__init__.py` with exports
24. **country/staff** - Created new `__init__.py` with exports
25. **country/tax** - Created new `__init__.py` with exports
26. **country/localization** - Created new `__init__.py` with exports
27. **country/payout** - Created new `__init__.py` with exports
28. **country/restriction** - Created new `__init__.py` with exports
29. **country/research** - Created new `__init__.py` with exports
30. **customers** - Added exports for all customer services
31. **security** - Added exports for core, fraud, detection, iam, threat, health, registration, ess
32. **security/core** - Added exports for security_service, security_metrics, kms_encryption
33. **security/fraud** - Added exports for fraud_service, fraud_engine, fraud_detection_service, impossible_travel_write_service
34. **security/detection** - Added exports for detection services
35. **security/iam** - Added exports for security_dependencies, iam_service
36. **security/threat** - Added exports for siem_engine, behavioral_analytics
37. **security/health** - Added exports for risk_controller, flat_risk_service
38. **security/registration** - Added exports for registration_service
39. **security/ess** - Added empty `__all__` (placeholder)
40. **audit** - Added exports for logs, data, compliance, and all audit services
41. **audit/logs** - Added exports for audit_service, audit_trail_service, audit_query_service, user_activity_tracker
42. **audit/data** - Added exports for data service
43. **audit/compliance** - Added exports for compliance audit_service
44. **hr** - Added exports for employees, hierarchy, payroll, performance, leave, learning, ess, shift, travel, succession, ghost_watchdog
45. **hr/travel** - Added exports for travel_service
46. **hr/succession** - Added exports for succession_service
47. **hr/shift** - Added exports for shift_roster_service
48. **hr/performance** - Added exports for performance_service, dei_auditor
49. **hr/payroll** - Added exports for payroll_service, payroll_engine
50. **hr/leave** - Added empty `__all__` (placeholder)
51. **hr/learning** - Added exports for lms_service
52. **hr/hierarchy** - Added exports for hierarchy_service
53. **hr/ghost_watchdog** - Added empty `__all__` (placeholder)
54. **hr/ess** - Added exports for ess_service
55. **hr/employees** - Added exports for risk_service, hse_manager, hr_service, employee_service, coi_service
56. **governance** - Added exports for settings, incident, command_center, auth, approval, admin, workflow_engine, operations, features
57. **governance/settings** - Added exports for misc_service, governance_package_service, admin_service
58. **governance/incident** - Added exports for incident_service
59. **governance/command_center** - Added exports for service, command_center_service, background
60. **governance/auth** - Added exports for iam_service_accounts
61. **governance/approval** - Created new `__init__.py` with exports for approval_matrix_service
62. **governance/admin** - Created new `__init__.py` with exports for bulk_ops_service, admin_service

---

## Summary

| Issue | Instances Found | Instances Fixed |
|-------|----------------|-----------------|
| Money as float | 6 | 6 |
| Hardcoded secrets | 0 (in production) | 0 |
| Duplicate logic | 2 pairs | 2 pairs |
| Missing __init__.py exports | 13 domains | 13 domains |

**Total files modified:** ~65
**Total files deleted:** 2 (placeholder duplicates)
