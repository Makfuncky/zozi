# Cash & Payment Management Cycle — Complete Audit & Gap Analysis

## File & Function Map

### LAYER 1: Bank Account Management

#### Backend Models
| File | Model/Class | Key Columns | Status |
|---|---|---|---|
| `backend/models/finance.py` | `BankStatementImport` | id, bank_name, file_name, period, total_lines, matched_lines, status | ✅ EXISTS |
| `backend/models/finance.py` | `BankStatementLine` | id, import_id, txn_date, description, amount, status (unmapped/mapped/reconciled) | ✅ EXISTS |
| `backend/models/finance.py` | `BankReconciliation` | id, statement_line_id, journal_entry_id, matched_amount, status, matched_at | ✅ EXISTS |
| `backend/models/finance.py` | `BankMappingRule` | id, match_pattern, description_contains, account_code, normal_side, priority | ✅ EXISTS |
| `backend/models/finance.py` | `BankAccount` | id, bank_name, account_name, account_number, iban, swift_bic, is_active | ✅ EXISTS |
| `backend/models/suppliers.py` | `SupplierBankAccount` (from db.models) | supplier_id, bank_name, beneficiary_name, iban, verification_status | ✅ EXISTS |
| `backend/models/payments.py` | `PaymentGatewayConnection` | provider_code, secret_key, public_key, webhook_secret, test_status | ✅ EXISTS |

**Missing**: No `LogisticsPartnerBankAccount` in models (handled at controller level only).

#### Backend Routers
| File | Endpoints | Status |
|---|---|---|
| `backend/routers/cash_management.py` | `GET/PUT /admin/bank-settings` | ✅ EXISTS |
| `backend/routers/admin_payouts.py` | `GET/POST /payouts/{country_code}`, `POST /verify`, `PUT /process` | ✅ EXISTS |
| `backend/routers/supplier_finance.py` | `GET/PUT /bank-account` | ✅ EXISTS |
| `backend/routers/logistics_partner.py` | `GET/PUT /me/bank-account` | ✅ EXISTS |

**Missing**: No `POST /admin/bank-accounts/upload-statement` for CSV/OFX import.

#### Frontend
| File | Purpose | Status |
|---|---|---|
| `frontend/web_app/src/app/admin/finance/BankAccountsPanel.tsx` | Zozi bank settings + pending verifications | ✅ EXISTS |
| `frontend/web_app/src/app/supplier/profile/page.tsx` | "Bank Details" tab with form | ✅ EXISTS |
| `frontend/web_app/src/app/logistics-partner/profile/page.tsx` | Operations tab with bank form | ✅ EXISTS |

**Missing**: Bank statement upload UI for admin.

### LAYER 2: Payment Processing

| File | Key Functions | Status |
|---|---|---|
| `backend/models/payments.py` | `Payment`, `PaymentReconciliationRun`, `PaymentGatewayConnection` | ✅ EXISTS |
| `backend/controllers/payments_controller.py` | Stripe/Tap/PayTabs integration, webhooks, payment status | ✅ EXISTS |
| `backend/services/payment_engine.py` | Payment intent, checkout sessions | ✅ EXISTS |
| `backend/services/payment_orchestrator.py` | Multi-step flows, gateway routing | ✅ EXISTS |
| `backend/routers/payments.py` | `POST /payments/charge`, webhook endpoints | ✅ EXISTS |

**Gaps**: None major — payment processing is well-implemented.

### LAYER 3: Settlements

| File | Model | Key Columns | Status |
|---|---|---|---|
| `backend/models/finance.py` | `SupplierSettlement` | supplier_id, order_id, gross_amount, commission_amount, vat_on_commission, net_amount, status, eligible_at, payout_id | ✅ EXISTS |
| `backend/models/finance.py` | `TransactionLedger` | user_id, supplier_id, logistics_partner_id, order_id, product_subtotal, discount_amount, delivery_charges, vat_amount, zozi_commission, net_supplier_amount, net_logistics_amount, cod_collected_amount | ✅ EXISTS |
| `backend/models/finance.py` | `RefundLedger` | order_id, customer_refund_amount, supplier_reversal, logistics_reversal, commission_reversal, vat_adjustment | ✅ EXISTS |

**Gap 🔴**: `SupplierSettlement` records are created but **nothing auto-creates the Payout when eligible_at is reached**.

### LAYER 4: Payout System

| File | Key Functions | Status |
|---|---|---|
| `backend/models/payments.py` | `Payout` (supplier_id, amount, method, status, reference) | ✅ EXISTS |
| `backend/models/payments.py` | `LogisticsPartnerPayout` (partner_id, amount, status, period) | ✅ EXISTS |
| `backend/models/finance.py` | `PayoutBatch`, `PayoutBatchItem` | ✅ EXISTS |
| `backend/services/payout_engine.py` | `calculate_supplier_payout()`, `get_payout_rate()`, `get_minimum_payout()` | ✅ EXISTS |
| `backend/services/treasury_engine.py` | `generate_payout_batch()`, `approve_payout_batch()` | ✅ EXISTS |
| `backend/routers/admin_payouts.py` | Admin payout CRUD, verify, process | ✅ EXISTS |
| `backend/routers/supplier_payouts.py` | Supplier payout list + request | ✅ EXISTS |
| `backend/routers/supplier_finance.py` | Payout status, order payment status | ✅ EXISTS |

**Gap 🔴**: **No auto-payout scheduler** — nothing periodically checks `SupplierSettlement.eligible_at` and creates Payout records. All payouts are admin-triggered.

### LAYER 5: Reconciliation

| File | Key Functions | Status |
|---|---|---|
| `backend/services/erp_finance_service.py` | `suggest_matches()` — amount ± date matching | ✅ EXISTS |
| `backend/services/erp_finance_service.py` | `match_statement_line()` — link statement to journal | ✅ EXISTS |
| `backend/services/erp_finance_service.py` | `auto_match_import()` — batch match all lines | ✅ EXISTS |
| `backend/routers/finance.py` | `POST /reconciliation/cod-remittance` — COD → Cash JE | ✅ EXISTS |
| `backend/routers/finance.py` | `GET /reconciliation/gateway-exceptions` | ✅ EXISTS |

**Gap 🔴**: No scheduled runner calls `auto_match_import()`. No bank statement upload UI.

### LAYER 6: Refund Process

| File | Key Functions | Status |
|---|---|---|
| `backend/models/finance.py` | `RefundLedger` with all reversal fields | ✅ EXISTS |
| `backend/routers/returns.py` | Return request CRUD | ✅ EXISTS |
| `backend/controllers/payments_controller.py` | Gateway refund calls | ✅ EXISTS |

**Gap 🔴**: No auto-wiring from return approval → RefundLedger creation → Payout reversal → Gateway refund.

---

## Gap Priority Matrix

| # | Gap | Severity | System Affected | Effort |
|---|---|---|---|---|
| 1 | **No auto-payout scheduler** — 10-day hold never triggers payout | 🔴 CRITICAL | Payout | 2-3 hours |
| 2 | **No bank statement upload UI** — admin can't upload CSV/OFX | 🔴 CRITICAL | Reconciliation | 4-6 hours |
| 3 | **No scheduled auto-reconciliation** — statements never auto-match | 🔴 CRITICAL | Reconciliation | 1-2 hours |
| 4 | **No COD auto-remittance** — delivery doesn't trigger reconciliation | 🟡 MAJOR | COD | 3-4 hours |
| 5 | **No refund auto-wiring** — return -> refund -> reversal | 🟡 MAJOR | Refunds | 4-5 hours |
| 6 | **No bank verification gate** — payout doesn't check verification | 🟡 MAJOR | Payout | 2-3 hours |
| 7 | **No end-to-end test** — order through payout | 🟡 MAJOR | All | 3-4 hours |

---

## Architecture Recommendation for Real Bank Connection

### Phase 1 — Complete The Foundations (Recommended Now)
```
Bank: CSV/OFX Download → Admin Upload → Auto-Reconcile → Verified
                                                                  ↓
Order → Settlement → 10-Day Hold → Auto-Check → Payout Created → Paid
                                                                  ↓
Return → RefundLedger → Reversal Created → Gateway Refund → Done
```

### Phase 2 — Add Bank API Connectivity (Future)
```
Bank API (OFX Direct / Open Banking) → Auto-Import → Auto-Reconcile
```

### Phase 3 — Add Real-Time Payouts (Future)
```
Stripe Connect / Tap Payout API → Verified Bank → Instant Payout
```

---

## Current Backend Health

| Check | Status |
|---|---|
| Backend routes loaded | ✅ 1500 routes |
| All cash/payment models import | ✅ Verified |
| `Payout.__table__.columns` | ✅ 19 columns including method |
| `SupplierSettlement.__table__.columns` | ✅ All financial fields present |
| Bank reconciliation service imports | ✅ Clean |
| Treasury engine imports | ✅ Clean |
