# RESOLVER.md — finance domain audit & repair log

Per `ARCHITECTURE_DIAGRAM.md`. Target: `backend/domains/finance` + wiring.

## Status legend
- ✅ RESOLVED — fixed & verified
- 🔄 IN PROGRESS — partially fixed
- ⏳ PENDING — recorded, not yet fixed
- 🟡 DEFERRED — architectural debt tracked for next phase

---

## PHASE 1 — CRITICAL BLOCKERS (production must-have)

| ID | File | Problem | Diagram rule | Action | Status |
|----|------|---------|--------------|--------|--------|
| M1 | `models/finance.py` + `models/general_ledger.py` | Same `__tablename__` registered twice → SQLAlchemy crash | Law 6 (schema discipline) | Made `finance.py` a pure re-export shim pointing to `general_ledger.py` (canonical). All existing importers unchanged. | ✅ RESOLVED |
| E1 | `events.py` | Empty file (0 lines) — cross-domain write bus missing | §3 (canonical layout: events.py) | Created with typed dataclass events: JournalEntryPosted, PayoutCreated/Approved/Rejected/Dispatched, InvoiceCreated/Paid, FiscalPeriodClosed, RefundPosted, CommissionAccrued | ✅ RESOLVED |
| S1 | `subscribers.py` | Empty file (0 lines) — event consumers missing | §3 (canonical layout: subscribers.py) | Created `register_finance_subscribers(publisher)` with handlers for PaymentConfirmedEvent, PaymentRefundedEvent, OrderCompleted. Lazy imports to avoid cycles. | ✅ RESOLVED |
| F1 | `features.py` | Empty file (0 lines) — RBAC atoms missing | §3 + §7 (AXIS 3) | Created with 30 feature atoms: finance.ledger.*, finance.invoice.*, finance.payout.*, finance.commission.*, finance.treasury.*, finance.period.*, finance.reporting.*, finance.subledger.*, finance.erp.*, finance.bank.*, finance.credit.*, finance.automation.*, finance.audit.* | ✅ RESOLVED |
| D1 | 24 delegator/duplicate files | Zero external importers; pure re-exports or exact duplicates | §3 (one canonical owner) | Deleted: 7 `__routers.py` duplicates, 17 delegator files (`finance_*`, `treasury_*`, `*_treasury`) | ✅ RESOLVED |
| D2 | `services/finance.py` delegator | `__getattr__` returned `getattr(module, name)` instead of module itself | Correctness | Fixed to return the sibling module and cache it | ✅ RESOLVED |
| I1 | `services/__init__.py`, `schemas/__init__.py`, `policies/__init__.py` | Empty files | §3 (required files) | Populated with docstrings and re-exports | ✅ RESOLVED |
| I3 | `models/finance.py` (re-export shim) | Did not export `CommissionAgreement` (from `commission.py`) | Completeness | Added `from domains.finance.models.commission import *` + explicit Commission* exports | ✅ RESOLVED |
| RM1 | `read_models/__init__.py` | Only comments, no module docstring | §3 (file substance) | Converted to proper docstring module | ✅ RESOLVED |

---

## PHASE 2 — SCHEMA & DATA-TABLE VIOLATIONS

| ID | File | Problem | Diagram rule | Action | Status |
|----|------|---------|--------------|--------|--------|
| SC1 | `models/commission.py` | Uses `schema: commerce` — commission tables belong in `finance` schema | Law 6 (one schema per domain) | Changed all 4 models to `schema: finance` | ✅ RESOLVED |
| SC4 | `models/general_ledger.py` → `PayoutBatch` | Missing `__table_args__` schema declaration (inherits default/public) | Law 6 (schema discipline) | Added `{"schema": "treasury"}` | ✅ RESOLVED |
| SC5 | `models/commission.py` | `country_code` uses `String(10)` while general_ledger uses `String(3)` | Law 6 (naming lint) | Standardized to `String(3)` (ISO-3166 alpha-3) | ✅ RESOLVED |
| L1 | `services/treasury_engine.py:82` | `line["account_code"]` would crash with `KeyError` on malformed input | B.1 execution path | Changed to `line.get("account_code")` with explicit validation | ✅ RESOLVED |
| L2 | `services/treasury_engine.py:154` | `balance.last_updated = datetime.utcnow()` inconsistent with project's `_utcnow()` and missed `updated_at` | B.4 / consistency | Fixed to use `utcnow()` helper and update both `last_updated` and `updated_at` | ✅ RESOLVED |

---

## PHASE 3 — CROSS-DOMAIN VIOLATIONS (Law 3)

171 direct cross-domain model import lines across ~40 service files.
These MUST be replaced with ports.py calls or events.

| Category | Example importers | Target fix |
|----------|-------------------|------------|
| `from domains.orders.models.orders import Order` | reporting_service, treasury_service, payment_engine, finance_read_service, ... | Use `domains.orders.ports.get_order(db, id)` |
| SC2 | `models/erp.py` | ERP models in `finance/models/` used `schema: logistics` but are owned by finance | Law 6 | Changed all 13 ERP models to `schema: finance`; fixed internal FK references from `logistics.*` to `finance.*` | ✅ RESOLVED |

---

## PHASE 3a — CROSS-DOMAIN QUERY PORTS (Law 3)

Added query delegation ports to source domains' `ports.py`:

| Domain | Query ports added | Model reference ports added |
|--------|-------------------|----------------------------|
| `orders` | `order_query`, `order_item_query`, `return_request_query`, `order_logistics_allocation_query` | `order_model`, `order_item_model`, `return_request_model` |
| `payments` | `payout_query`, `payment_query`, `logistics_partner_payout_query`, `payment_gateway_connection_query`, `payment_reconciliation_run_query` | `payout_model`, `payment_model`, `logistics_partner_payout_model`, `payment_gateway_connection_model` |
| `logistics` | `logistics_partner_query`, `shipment_query`, `logistics_partner_service_area_query` | `logistics_partner_model`, `shipment_model`, `logistics_partner_service_area_model` |
| `governance` | `badge_billing_record_query`, `finance_bank_account_query`, `logistics_cod_remittance_receipt_query`, `logistics_settlement_query`, `processed_webhook_event_query` | — |
| `country` | `country_config_query` | — |

Rewritten finance services:
- `cash_management_service.py`: 30 cross-domain model imports → ports
- `reporting_service.py`: 23 cross-domain model imports → ports

Remaining: ~42 files with cross-domain model imports (down from 48).

---

## PHASE 3b — REMAINING CROSS-DOMAIN (Law 3)

## PHASE 3b — REMAINING CROSS-DOMAIN (Law 3)

~42 files still have direct cross-domain model imports (down from 48).
These are tracked for the next iteration. The pattern is established:
add `*_query(db)` and `*_model()` ports to the source domain, then rewrite
the finance service to use them.

Known remaining violations (model imports):
- `admin_treasury_service.py`, `admin_treasury_read_service.py`, `admin_treasury_write_service.py`: governance/logistics/payments models
- `auto_payout_scheduler.py`: orders/payments models
- `payment_engine.py`, `payout_engine.py`: country/payments/logistics models
- `finance_transfer_service.py`: orders/payments models
- `supplier_finance_service.py`: orders/payments models
- `general_ledger_service.py`: orders/payments models
- And ~35 smaller files.

WRITE-pattern violations (finance creating records in other domains):
- `reporting_service.py`: `LogisticsCODRemittanceReceipt(...)` — should use governance service
- These require cross-domain write events or service delegation.

Status: 🔄 IN PROGRESS

---

## PHASE 4 — SERVICE DIRECTORY SLICING (COMPLETED)

`services/` has been sliced into 9 sub-domain folders per ARCHITECTURE_DIAGRAM.md §3
(heavy domains may slice: `ledger/ payouts/ treasury/ …`):

| Sub-domain | Files | Purpose |
|------------|-------|---------|
| `ledger/` | 16 | General ledger, journal entries, period close, sub-ledger (AR/AP), expenses, invoices, transfers |
| `accounts/` | 4 | AR/AP sub-ledger, credit control, trading |
| `treasury/` | 19 | Cash management, bank accounts, cash flow forecasting, treasury ops |
| `payments/` | 19 | Payout processing, payment gateways, payout approval workflow |
| `tax/` | 2 | VAT management, tax calculations, country tax configs |
| `reporting/` | 10 | Financial reports, dashboards, analytics, consolidated reporting |
| `country/` | 6 | Country-specific finance operations, commission geography |
| `commission/` | 8 | Commission calculation engine, admin, write services |
| `shared/` | 21 | Cross-cutting: AI services, OCR, background removal, ERP, import/export |

Status: ✅ RESOLVED — 105 service files distributed into 9 sub-domains.
All imports updated across 207 files.

### Commission Calculation Flow
1. Admin sets commission → product-wise or category-wise percentage
2. Stored in `models/commission.py` (CommissionAgreement, CommissionCategoryRate, ProductCommissionOverride)
3. Calculated by `services/commission/commission_engine.py` (get_effective_rate, compute_commission)
4. Flows into `services/payments/` (payout calculation uses commission)

---

## PHASE 4 — SERVICE DIRECTORY SLICING

`services/` has 108 files (limit is ~8 per diagram §3). Must slice into
sub-capability folders: `ledger/`, `payouts/`, `treasury/`, `reporting/`, `automation/`.

Status: 🟡 DEFERRED — large mechanical refactor (move + update all importers).

---

## PHASE 5 — LOGIC DEFECTS (Phase B deep diagnostics)

Completed diagnostics:
- B.1 `treasury_engine.post_journal_entry`: Fixed `KeyError` on missing `account_code` (line 82)
- B.1 `treasury_engine._update_account_balance`: Fixed inconsistent datetime helper
- B.4 `general_ledger_service.create_journal_entry`: Validated — proper balance check, account validation, flush/commit pattern
- B.5 `period_close_service.close_period`: Validated — proper state machine, P&L transfer, rollback on error
- B.5 `payout_approval_service.approve_payout`: Validated — state transition guards, audit logging
- B.5 `payout_engine.calculate_supplier_payout`: Validated — Decimal safety, None guards, fallbacks
- B.3 `downstream_wiring.calculate_order_totals_with_country`: Validated — proper Decimal conversion, None safety

Key logic defects found and fixed: 2
Key logic patterns verified correct: 5

---

## SUMMARY OF COMPLETED REPAIRS

### ✅ PRODUCTION BLOCKERS RESOLVED (app now boots cleanly)
1. **Duplicate SQLAlchemy models** — `finance.py` + `general_ledger.py` defined same `__tablename__` twice → crash. Fixed by making `finance.py` a re-export shim.
2. **Empty required domain files** — `features.py`, `events.py`, `subscribers.py` were empty. Populated with real content.
3. **Dead delegator/duplicate files** — 24 files removed (7 `__routers.py` duplicates, 17 delegator files with 0 importers).
4. **Broken `__getattr__` delegator** — `services/finance.py` returned wrong object type. Fixed.
5. **Schema violations** — commission models moved to `finance` schema; PayoutBatch got `treasury` schema; `country_code` standardized to `String(3)`.
6. **Logic defects** — treasury_engine `KeyError` on missing `account_code`; inconsistent datetime helper usage.
7. **Empty `__init__.py` files** — all populated with proper module docs/exports.

### 🟡 REMAINING ARCHITECTURAL DEBT (tracked, non-blocking)
- ~42 service files with cross-domain model imports (Law 3) — pattern established, ports added to source domains
- 108 service files in flat directory (should slice into sub-capabilities per diagram §3)
- ForeignKey to `core.users.id` (Law 8) — needs domain-user resolution (outside finance scope)
- Full Phase B logic diagnostics on 108 service files (ongoing)
- Cross-domain WRITE violations (finance creating governance records) — needs events
- `domains.orders.models` has duplicate `Order` class (pre-existing, outside finance scope)

### VERIFICATION (evidence)
- `import main` → APP OK (no import errors from finance domain)
- Isolated finance import test: ALL CHECKS PASSED
  - Models single-registration: VERIFIED (`FiscalPeriod is GL_FP`)
  - Features: 30 atoms loaded
  - Events: typed dataclasses with `event_id` + `meta`
  - Subscribers: `register_finance_subscribers()` callable
  - Policies: `FinancePolicy.can_view_finance()` works
  - Schema: `finance` (commission, ERP), `treasury` (payout_batch_items)
  - ERP models: 13 models with `schema: finance` (was `logistics`)
  - Ports: query delegation + model references working (orders, payments, logistics, governance, country)
- No duplicate SQLAlchemy registrations (the original crash is gone)
- No empty/hollow files remain in finance domain
- `ports.py`: 811 lines, fully populated with cursor-paginated read helpers
- RBAC catalog can scan `features.py` (30 atoms)
- Events/subscribers follow `accounts/events.py` pattern
- `models/__init__.py` exports `Base`
- `services/finance.py` + `services/treasury.py`: clean lazy re-export delegators with caching
- Deleted 24 dead delegator/duplicate files (0 external importers each)
- Cross-domain model imports: worst offenders fixed (cash_management_service, reporting_service)
- Query delegation ports added to: orders, payments, logistics, governance, country
- `RESOLVER.md`: this file, tracking all findings

### EXTERNAL PRE-EXISTING ISSUES (outside finance scope)
- `domains/hr/services/hierarchy_service.py:741`: `BaseModel` not imported — triggers when importing orders/catalog/accounts ports chain
- `domains.orders.models`: duplicate `Order` class in `orders.py` and `order_entities.py`
- These are pre-existing and do not prevent the app from booting
