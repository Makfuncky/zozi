# ZOZI SCOPE · 04 — FINANCE DOMAIN (LEDGER, PAYMENTS, PAYOUTS)
**Document type:** Scope-binding specification — **single source of truth** for the Finance domain.
**Version:** 1.0 · **Status:** DRAFT → needs founder sign-off · **Owner:** Finance / Treasury
**Last reviewed:** 2026-08-05
**Supersedes:** none. **Must cite & never contradict:** `01_DATABASE.md`, `layer_rules.yaml`, `repo_structure.yaml`.

> **Honesty notes (baked in, never papered over):**
> - This document was authored to satisfy audit finding **PF2** (`documents/scope/04_FINANCE.md` missing). It describes the *as-built* Finance domain, not an aspirational redesign.
> - Cross-ecosystem references from `finance.*` tables to `orders.*`, `core.users`, `country.country_configs`, and `treasury.*` are **intentional and by-design** (shared reference schemas, not duplicated data). The DATABASE audit may flag some as DB06; they are retained deliberately.
> - Items marked **[CONFIRM]** require real product values; left blank rather than fabricated.

---

## 1. Overview

### 1.1 Feature title
ZOZI Finance — the double-entry ledger, accounts receivable / payable, payments capture, payouts, commission, and tax engine that underpins every commerce transaction.

### 1.2 Objective / purpose
Provide one authoritative financial substrate (chart of accounts, journal entries, balances, AR/AP aging, payment capture, supplier/customer payouts, commission and tax calculation) so every surface (customer, supplier, admin, treasury) operates on one bounded context (`finance`) with one set of rules.

### 1.3 Scope
**In scope:** chart of accounts, journal entries & reversals, trial balance / account balances, AR & AP, payment gateway orchestration, payout batching, commission engine, tax service, financial reporting.
**Out of scope (own scope docs):** treasury cash positioning & bank transfer execution → treasury scope; orders lifecycle → `05_ORDERS.md`; search/merchandising → `02_SEARCH.md`; supplier onboarding → supplier scope.

### 1.4 Scope boundary (crisp ✔ / ✘)
```
IN THIS DOCUMENT (finance)                 NOT HERE
✔ Chart of accounts & journal entries      ✘ Bank transfer execution   → treasury scope
✔ AR / AP invoices & aging                 ✘ Shipment tracking         → logistics scope
✔ Payment gateway capture (Stripe/PayPal/Thawani) ✘ Catalogue pricing  → 02_SEARCH
✔ Supplier / customer payout batching      ✘ User auth                 → security scope
✔ Commission & tax calculation             ✘ Country config internals  → country scope
```

### 1.5 Business value / KPIs
- Every posted movement is double-entry balanced and reversible via `je_reversal_service`.
- Payments are captured and reconciled through a single `payments_gateway_service` façade.
- Payouts are batched and auditable per supplier.

---

## 2. Architecture & Design

### 2.1 Bounded context
Finance lives in the **finance** ecosystem. Primary tables/models:
| Table | Model | Role |
|-------|-------|------|
| `gl_accounts` | `GLAccount` | Chart of accounts |
| `journal_entries` | `JournalEntry` | Ledger header (double-entry) |
| `journal_entry_lines` | `JournalEntryLine` | Debit/credit lines |
| `ar_invoices` | `ARInvoice` | Accounts receivable |
| `ap_payables` | `APPayable` | Accounts payable |
| `payments` | `Payment` | Captured payments |
| `commissions` | `Commission` | Earned commission |

### 2.2 Layer rules (enforced)
Finance follows the standard layered architecture (`layer_rules.yaml`):
- **Models** `models/finance/` → **Services** `services/finance/` → **Controllers** `controllers/finance/` → **Routers** `routers/*finance*`.
- Routers generally call controllers (e.g. `accounting_controller`, `commission_controller`, `payments_controller`); a number of finance routers still call services directly (audit **CIR2** — tracked platform-wide, not Finance-specific).

---

## 3. Ledger & Reversals

- `accounting_controller` seeds the chart of accounts, lists accounts, creates journal entries, and produces trial balances / account balances.
- `je_reversal_service.reverse_journal_entry` creates a mirror entry with opposite sides, linked via `reversal_of_id`. Queries are bounded (filtered by `entry_id`, capped at 1000 lines — audit **PERF4** remediation).
- The models package exposes a ledger façade (`data/ledger_facade.py`) used by services to keep writes consistent.

---

## 4. Payments & Payouts

- `payments_gateway_service` is the single capture/orchestration façade for Stripe, PayPal, and Thawani (webhooks + confirm paths).
- Payouts are batched (jobs + services) and auditable; treasury executes the actual bank transfer (`finance_transfer_service` + treasury providers).
- `commission_engine` computes effective commission rates; `tax_service` computes tax.

---

## 5. Reporting

- `financial_reporting` and `analytics/financial_reports_service` produce balances, cash-flow, and aging reports.
- Both share a `_get_account_balances_for_period` helper (private, used across the finance/analytics boundary — audit **API2**, tracked as a cross-domain coupling).

---

## 6. Appendices

### Appendix A — Model → Table map
See §2.1. Models in `backend/models/finance/`.

### Appendix B — Open findings (tracked, not yet fixed)
- **A2** (yellow): `accounting_controller.py` and `je_reversal_service.py` flagged with no inbound imports — **false positive**; both are imported by `controllers/__init__.py` and `*finance*_routes` routers. Verified, left intact.
- **SYM1** (yellow): `CommissionResult`, `ConfiguredBankApiTransferProvider`, `FinanceAIResult`/`FinanceAiProviderSettings`, and the `*Body` request models in finance routers are flagged as unused — **false positive**; all are used within their own module (return types / FastAPI route bodies). Verified, left intact.
- **API2** (yellow): `_parse_date` (finance_automation) and `_get_account_balances_for_period` (financial_reporting / analytics) flagged as private symbols used externally — internal/cross-module usage; rename deferred as a low-value cross-domain change.
- **CA1 / CA2 / CIR2 / DG2 / DOM2 / MV1 / DOM7 / Q1 / QUAL3 / SYM2 / FE3** (yellow): cross-cutting architecture findings spanning many domains; addressed at platform level, not here.
