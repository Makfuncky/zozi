# Finance Domain — Complete Diagnosis Report

> Generated: 2026-08-27  
> Scope: `backend/domains/finance/` — Full Stack  
> Reference: ARCHITECTURE_DIAGRAM.md §13  
> Total issues found: **150+**

---

## Executive Summary

| Severity | Count |
|----------|-------|
| 🔴 CRITICAL | 30+ |
| 🟠 HIGH | 50+ |
| 🟡 MEDIUM | 40+ |
| 🟢 LOW | 25+ |
| **TOTAL** | **150+** |

---

## 1. CRITICAL — Syntax/Import Errors (File Won't Load)

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 1 | `treasury_service.py` | 15 | **IndentationError** + `TreasuryAdapter` not imported | Fix indent + import |
| 2 | `admin_commission_service.py` | 46, 88 | **SyntaxError**: `q * page_size).limit(...)` | Add missing `.offset()` |
| 3 | `payment_engine.py` | 98, 1004 | `round_money` commented out but used | Uncomment `kernel.money` import |
| 4 | `payout_batch_service.py` | 7-16 | `PaymentResult`, `RefundResult`, etc. not imported | Add imports |
| 5 | `admin_cash_service.py` | 14-17, 41, 64 | `create_cash_account_model` undefined | Define or import |
| 6 | `admin_finance_creation_service.py` | 13-27 | Imports 8 names from `ports.py` that don't exist | Create or fix |
| 7 | `cash_management_service.py` | 42-135 | **30+ methods return `{}` or `[]`** | Implement real logic |
| 8 | `cash_management_service.py` | 102-104 | `admin_record_cod_remittance` returns fake `SimpleNamespace` | Persist to DB |
| 9 | `cash_management_service.py` | 134-135 | `log_refund_bank_transaction` is `pass` | Implement |
| 10 | `payout_batch_service.py` | 489-496 | `PaymentEngine.__init__` defined twice | Remove duplicate |
| 11 | `employee/routers/finance.py` | 20-29 | `accounting_controller` doesn't exist | Create controller |
| 12 | `employee/routers/finance.py` | 611 | `cash_management_controller` doesn't exist | Create controller |
| 13 | `employee/routers/finance.py` | 1217 | `invoice_controller` doesn't exist | Create controller |
| 14 | `employee/routers/finance.py` | 39 | `reverse_journal_entry` wrong import path | Fix to `je_reversal_service` |
| 15 | `logistics/routers/finance.py` | — | **FILE DOES NOT EXIST** | Create |

---

## 2. CRITICAL — Broken FK References

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 16 | `general_ledger.py` | 88 | FK `treasury.payouts.id` — table doesn't exist | Change to `finance.payouts.id` |
| 17 | `general_ledger.py` | 501 | FK `treasury.cash_accounts.id` | Change to `finance.cash_accounts.id` |
| 18 | `general_ledger.py` | 549-551 | FK `treasury.treasury_accounts.id` (3×) | Change to `finance.treasury_accounts.id` |
| 19 | `general_ledger.py` | 594 | FK `treasury.treasury_accounts.id` | Change to `finance.treasury_accounts.id` |
| 20 | `general_ledger.py` | 612 | FK `treasury.payment_gateway_connections.id` | Change to `finance.payment_gateway_connections.id` |

---

## 3. CRITICAL — Cross-Domain Pollution

| # | File | Line | Violation | Fix |
|---|------|------|-----------|-----|
| 21 | `models/erp.py` | all | **ERP/procurement models in finance** | Move to `domains/inventory/` or `domains/procurement/` |
| 22 | `finance_service.py` | 288-306 | Imports from 6 other domains | Use ports |
| 23 | `payment_engine.py` | 79-93 | Imports from catalog, comms, country, orders | Use ports |
| 24 | `payroll_wrapper.py` | 4 | Imports from `domains.hr` | **Law 1 violation** — move to HR |
| 25 | `gateway_*.py` | many | 15+ direct imports of `comms.services` | Use events |

---

## 4. SECURITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 26 | `gateway_tap.py` | 1010-1023 | Webhook accepts unsigned requests when secret not set | Reject when no secret |
| 27 | `gateway_tap.py` | 1430-1438 | Same for Thawani webhook | Reject when no secret |
| 28 | `payment_orchestrator.py` | 814-820 | Signature check skipped when `webhook_secret` empty | Reject |
| 29 | `payment_orchestrator.py` | 1655-1687 | `extra_config` JSON drives URLs/headers — template injection | Validate schema |
| 30 | `general_ledger_service.py` | 1741-1744 | PII (account_number, IBAN) in plaintext CSV export | Mask or encrypt |
| 31 | `payment_engine.py` | 184-185 | Module-level globals not thread-safe | Use `threading.Lock` |
| 32 | `finance_service.py` | 273-275 | Returns tuple instead of `HTTPException` | Raise proper exception |

---

## 5. SCALABILITY ISSUES

| # | File | Line | Issue | Fix |
|---|------|------|-------|-----|
| 33 | `payment_orchestrator.py` | 1504 | Full table scan on `GatewaySettlementSchedule` | Add filters |
| 34 | `payment_orchestrator.py` | 1523-1561 | Loads all COD orders into memory | Batch processing |
| 35 | `payout_batch_service.py` | 54-78 | Loads ALL pending settlements into memory | Use pagination |
| 36 | `payout_batch_service.py` | 898-913 | Single transaction locks thousands of rows | Batch with `LIMIT` |
| 37 | `payment_engine.py` | 4673 | **Mega-file** — 4,673 lines, 6+ concerns | Split into focused services |
| 38 | `general_ledger_service.py` | 2676 | **Mega-file** — 2,676 lines, 6+ concerns | Split into focused services |
| 39 | `payout_batch_service.py` | 1300 | **Mega-file** — 1,300 lines, 5+ concerns | Split into focused services |
| 40 | `payment_orchestrator.py` | 1763 | **Mega-file** — 1,763 lines, 4+ concerns | Split into focused services |

---

## 6. MISSING FUNCTIONALITY (17 GAPS)

### 6.1 CRITICAL (4 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 41 | **Financial Reporting** (P&L, Balance Sheet, Cash Flow) | `services/reporting/financial_reporting.py` |
| 42 | **FX Rate Table** (live multi-currency) | `FxRate` model + `providers/finance/fx_rates.py` |
| 43 | **Dunning Engine** (AR collections) | `services/collections/dunning_service.py` |
| 44 | **AP Aging + Payment Runs** | `services/ap/ap_aging_service.py` + `payment_run_service.py` |

### 6.2 HIGH (4 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 45 | **Tax Engine** (VAT/GST/sales tax) | `services/tax/tax_engine.py` + models |
| 46 | **Fixed Asset Depreciation** | `services/ledger/depreciation_service.py` |
| 47 | **AML/KYC Sanctions Screening** | `AmlScreeningCheck` model + hook into `approve()` |
| 48 | **SOX Maker-Checker Controls** | `ApprovalPolicy` model + enforce in `create_journal_entry` |

### 6.3 MEDIUM (4 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 49 | **Cost-Center Allocation** | `services/ledger/allocation_service.py` |
| 50 | **Recurring Journal Templates** | `services/ledger/recurring_service.py` |
| 51 | **Inter-Company Transfers** | `InterCompanyTransfer` model + service |
| 52 | **Sub-Ledger Controller** | `services/ledger/sub_ledger_controller.py` |

### 6.4 LOW (5 gaps)

| # | Gap | Implementation |
|---|-----|----------------|
| 53 | **Cash-Flow Forecasting** | `services/treasury/cash_flow_forecast_service.py` |
| 54 | **Commission Engine** | `services/commission/commission_engine.py` |
| 55 | **Payroll Relocation** | Move to `domains/hr/` |
| 56 | **GDPR Financial Data Retention** | `services/compliance/gdpr_service.py` |
| 57 | **Cash CQRS Split** | Split `CashManagementService` |

---

## 7. KERNEL, RBAC, PROVIDER, INFRASTRUCTURE CONNECTIONS

### 7.1 Kernel (INCONSISTENT)

| # | Issue | Fix |
|---|-------|-----|
| 58 | `kernel.money` import commented out in `payment_engine.py` | Uncomment |
| 59 | `float` used for money in 15+ service files | Use `Decimal` |
| 60 | No `kernel.period` usage | Create `kernel.period` |

### 7.2 RBAC (MISSING)

| # | Issue | Fix |
|---|-------|-----|
| 61 | `finance_service.py` calls `require_permission` 30+ times | Move to routers |
| 62 | No `require_feature()` anywhere | Wire in routers |
| 63 | `admin_cash_service.py` has no RBAC | Add auth |

### 7.3 Providers (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 64 | Only `providers.finance.bank_api` used | Add `providers.finance.fx_rates` |
| 65 | No `HAS_STRIPE` availability check | Add flag |

### 7.4 Infrastructure (INCOMPLETE)

| # | Issue | Fix |
|---|-------|-----|
| 66 | No Redis cache on hot paths | Add caching |
| 67 | No tracing/metrics | Add `with_tracing()` |
| 68 | Thread-unsafe module globals | Use locks |

---

## Priority Action Plan

### Phase 1: CRITICAL (Fix Immediately)

| # | Action |
|---|--------|
| 1 | Fix syntax errors in `admin_commission_service.py`, `treasury_service.py` |
| 2 | Uncomment `kernel.money` import in `payment_engine.py` |
| 3 | Fix 5 broken FK references (`treasury.*` → `finance.*`) |
| 4 | Implement `log_bank_transaction` (currently stub) |
| 5 | Replace 30+ stubs in `cash_management_service.py` |
| 6 | Create missing controllers (`accounting`, `cash_management`, `invoice`) |
| 7 | Create missing `logistics/routers/finance.py` |
| 8 | Move `payroll_wrapper.py` to `domains/hr/` |
| 9 | Move ERP models out of finance |
| 10 | Fix webhook signature verification |

### Phase 2: HIGH (Fix This Week)

| # | Action |
|---|--------|
| 11 | Split mega-files (`payment_engine.py`, `general_ledger_service.py`) |
| 12 | Replace direct cross-domain imports with ports/events |
| 13 | Add RBAC at router layer |
| 14 | Add pagination to all list endpoints |
| 15 | Add Pydantic schemas to all endpoints |
| 16 | Implement Financial Reporting service |
| 17 | Implement FX Rate table + provider |
| 18 | Implement Dunning engine |
| 19 | Implement AP aging + payment runs |

### Phase 3: MEDIUM (Fix This Month)

| # | Action |
|---||--------|
| 20 | Add missing `ondelete` to all FKs |
| 21 | Add `updated_at` to 3 models |
| 22 | Fix `origin_country` width to String(2) |
| 23 | Add Tax Engine |
| 24 | Add Depreciation scheduler |
| 25 | Add AML screening |
| 26 | Add SOX maker-checker controls |

---

## Statistics

| Metric | Value |
|--------|-------|
| Total files | 27+ |
| CRITICAL issues | 30+ |
| HIGH issues | 50+ |
| MEDIUM issues | 40+ |
| LOW issues | 25+ |
| Syntax errors | 3 |
| Broken FKs | 5 |
| Stub methods | 30+ |
| Mega-files (>1000 lines) | 4 |
| Missing routers | 1 |
| Missing functionality gaps | 17 |
| Security vulnerabilities | 7 |
| Thread-unsafe globals | 2 |
