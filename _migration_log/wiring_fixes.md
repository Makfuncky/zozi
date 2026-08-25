# Wiring Fixes — events.py, ports.py, features.py

**Date:** 2026-08-26
**Agent:** Wiring Fix Agent

## Summary

Added missing `events.py`, `ports.py`, and `features.py` files to domain `services/` directories following existing codebase conventions (Law 3 cross-domain patterns).

## Files Created

### Task 1: events.py (7 files)

| Domain | Path | Events |
|--------|------|--------|
| analytics | `domains/analytics/services/events.py` | ReportGenerated, NewsPublished, SimulationCompleted |
| audit | `domains/audit/services/events.py` | AuditLogged, AnomalyDetected, ComplianceViolation |
| finance | `domains/finance/services/events.py` | InvoiceIssued, PaymentProcessed, PayoutCompleted, CommissionCalculated |
| hr | `domains/hr/services/events.py` | EmployeeOnboarded, EmployeeOffboarded, LeaveRequested, PayrollProcessed |
| orders | `domains/orders/services/events.py` | OrderCreated, OrderConfirmed, OrderShipped, OrderDelivered, OrderCancelled |
| promotions | `domains/promotions/services/events.py` | CouponApplied, PromotionActivated, PromotionExpired |
| suppliers | `domains/suppliers/services/events.py` | SupplierRegistered, SupplierVerified, SupplierSuspended |

### Task 2: ports.py (6 files)

| Domain | Path | Key Functions |
|--------|------|---------------|
| analytics | `domains/analytics/services/ports.py` | read_executive_news, read_predictive_simulations, get_financial_report_by_id, list_financial_reports |
| audit | `domains/audit/services/ports.py` | get_audit_log_by_id, list_audit_logs, list_audit_logs_by_entity, list_audit_logs_by_user, get_command_center_view_by_id, list_command_center_views_by_user |
| hr | `domains/hr/services/ports.py` | get_employee_by_id, get_employee_by_user_id, list_employees, get_employee_attendance_by_id, list_employee_leave_requests, list_employee_documents, get_org_unit_by_id, list_active_org_units, get_office_by_id, list_offices |
| logistics | `domains/logistics/services/ports.py` | get_logistics_partner_by_id, list_logistics_partners, get_logistics_partner_profile_by_id, list_logistics_partner_profiles, get_logistics_pricing_profile_by_id, list_logistics_pricing_profiles, get_shipment_by_id, list_shipments, get_shipment_event_by_id, list_shipment_events |
| promotions | `domains/promotions/services/ports.py` | get_promotion_engine_config, is_engine_enabled, get_max_combined_discount |
| suppliers | `domains/suppliers/services/ports.py` | get_supplier_profile_by_user, get_supplier_profile_by_id |

### Task 3: features.py (10 files)

| Domain | Path | Feature Count |
|--------|------|---------------|
| analytics | `domains/analytics/services/features.py` | 7 atoms (reports.read, reports.generate, news.read, news.publish, simulations.read, simulations.run, export) |
| audit | `domains/audit/services/features.py` | 8 atoms (logs.read, logs.export, anomalies.read, anomalies.manage, compliance.read, compliance.manage, command_center.read, command_center.configure) |
| comms | `domains/comms/services/features.py` | 8 atoms (messages.read, messages.send, tickets.read, tickets.create, tickets.manage, notifications.read, notifications.send, broadcast) |
| country | `domains/country/services/features.py` | 7 atoms (read, manage, currency.configure, tax.configure, cross_border.read, cross_border.manage, rls.configure) |
| finance | `domains/finance/services/features.py` | 10 atoms (invoices.read, invoices.manage, payments.read, payments.process, payouts.read, payouts.manage, commissions.read, commissions.manage, general_ledger.read, bank_reconciliation) |
| governance | `domains/governance/services/features.py` | 8 atoms (roles.read, roles.manage, permissions.read, permissions.assign, policies.read, policies.manage, user.ban, moderation) |
| hr | `domains/hr/services/features.py` | 12 atoms (employees.read, employees.manage, attendance.read, attendance.manage, leave.read, leave.manage, payroll.read, payroll.manage, org_structure.read, org_structure.manage, training.read, training.manage) |
| orders | `domains/orders/services/features.py` | 8 atoms (read, create, manage, cancel, fulfill, returns.read, returns.manage, export) |
| promotions | `domains/promotions/services/features.py` | 8 atoms (coupons.read, coupons.manage, campaigns.read, campaigns.manage, engine.configure, discounts.read, discounts.manage, analytics) |
| suppliers | `domains/suppliers/services/features.py` | 9 atoms (profiles.read, profiles.manage, verification, catalog.read, catalog.manage, orders.read, orders.manage, analytics, badges.manage) |

## Domains Covered

- **analytics**: events + ports + features
- **audit**: events + ports + features
- **comms**: features (events already existed)
- **country**: features (events already existed)
- **finance**: events + features (ports already existed at domain level)
- **governance**: features
- **hr**: events + ports + features
- **logistics**: ports + features (events already existed)
- **orders**: events + features (ports already existed at domain level)
- **promotions**: events + ports + features
- **suppliers**: events + ports + features

## Notes

- `catalog` and `governance` domains were not in scope for events.py/ports.py additions per task spec.
- Existing domain-level `ports.py` files (at `domains/{domain}/ports.py`) remain intact; new `services/ports.py` files mirror the sanctioned read surface for service-layer consumers.
- All events.py files follow the frozen-dataclass pattern with `serialize()` method and best-effort `publish_*` helpers.
- All features.py files follow the `FEATURES` dict + `all_features()` + `is_known()` pattern with wildcard prefix support.
