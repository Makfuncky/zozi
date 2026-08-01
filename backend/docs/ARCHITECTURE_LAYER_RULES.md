# Architecture Layer Rules — Allowed Cross-Domain Imports

This document records **explicitly allowed** cross-domain imports that the auto-scanner
flags as DG3 violations. These are legitimate business requirements, not architectural
debt.

## Finance → Other Domains

| Source Module | Import | Target | Justification |
|---|---|---|---|
| `services/cash_management_service.py` | `logistics_partner_pricing` | Logistics | COD calculations need country-specific logistics pricing |
| `services/cash_management_service.py` | `supplier_badge_service` | Supplier | Badge recalculation triggered after financial settlements |
| `services/cash_management_service.py` | `admin_analytics_service` | Admin | Financial snapshots refresh admin dashboard analytics |
| `services/cash_management_service.py` | `retention_service` | Shared | Operational retention runs as part of daily automation |
| `services/commission_engine.py` | `logistics_partner_pricing` | Logistics | Commission rates depend on country-specific logistics costs |
| `services/finance_transfer_service.py` | `logistics_partner_pricing` | Logistics | Transfer exports need logistics pricing metadata |
| `services/payout_batch_service.py` | `transactional_email_service` | Email | Payout confirmations trigger email notifications |
| `services/treasurer.py` | `employee_models` | HR | Treasury needs employee data for salary disbursement |
| `services/treasury_service.py` | `employee_models` | HR | Treasury journal entries reference employee records |

## Intra-Domain (Finance → Finance)

These are NOT cross-domain — they are within the finance bounded context:

| Source Module | Import | Target |
|---|---|---|
| `services/cash_management_service.py` | `finance_transfer_service` | Finance |
| `services/cash_management_service.py` | `bank_transaction_service` | Finance |
| `services/cash_management_service.py` | `general_ledger_service` | Finance |
| `services/financial_reporting.py` | `financial_reports_service` | Finance |

## Service → Controller (W3 Exception)

| Source Module | Import | Target | Justification |
|---|---|---|---|
| `services/finance/payments_service.py` | `controllers.payments_controller` | Controller | Transitional re-export layer — business logic migration in progress (see TODO in file) |

## Re-Export Shims (DG3 False Positives)

The auto-scanner flags these thin re-export files as DG3 violations because they
import from modules outside their subfolder. They are NOT real cross-domain imports —
they are backward-compatible shims that re-export from the canonical location.

| Shim Location | Canonical Location | Pattern |
|---|---|---|
| `services/finance/*.py` (11 files, ~140B each) | `services/*.py` | `from services.X import *` |
| `services/treasury/*.py` (6 files, ~140B each) | `services/*.py` | `from services.X import *` |
| `controllers/admin/*.py` | `controllers.security.*` and `controllers.catalog.*` | `from controllers.security X import Y`; `from controllers.catalog X import Y` |
| `controllers/admin/__init__.py` | `controllers.admin.*` + `controllers.security.*` + `controllers.catalog.*` | `from .X import *`; `from controllers.Y.Z import *` |
| `controllers/admin_controller.py` | `controllers.admin.*` + `controllers.security.permissions` | `from controllers.admin import *`; `from controllers.security.permissions import X` |
| `controllers/supplier/__init__.py` | `controllers.supplier.supplier_controller` | `from .supplier_controller import *` |
| `controllers/commerce/__init__.py` | `controllers.commerce.package` | package-level re-export pattern |
| `controllers/communication/notifications_controller.py` | `controllers.communication` | notification functions re-export |
| `controllers/mobile_controller.py` | `controllers.communication` | mobile-specific communication layer |

These shims exist for backward compatibility. They should NOT be counted as
architecture violations in future scans.

## Policy

- **Intra-domain imports** (finance → finance) are always allowed without documentation.
- **Cross-domain imports** must be documented here with a business justification.
- **Service → Controller imports** (W3) must be documented and have an active migration plan.
- **Re-export shims** are not violations — they are backward-compatible re-exports.
- New cross-domain imports require updating this file before merge.
