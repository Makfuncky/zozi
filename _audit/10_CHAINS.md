# Chains

Generated: 2026-09-30T04:40:00Z
Run number: 1

## CHAIN-001: Customer order placement (multi-supplier)

- **Features involved:** [F-CUST-006, F-CUST-007, F-CUST-010, F-INF-008, F-INF-014]
- **Actors involved:** [customer, supplier, logistics, admin]
- **Domains involved:** [orders, payments, inventory, logistics]
- **Entry point:** POST /api/v1/customer/checkout
- **Exit state:** Order created, payment captured, stock reserved, shipment assigned
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Customer | Checkout | Address → Delivery → Payment → Confirm | F-CUST-006 |
| 2 | Customer | Payment — Card | 3DS/confirm → webhook → order finalized | F-CUST-007 |
| 3 | System | Event Bus | payment.captured event emitted | F-INF-008 |
| 4 | System | Notification Engine | WS push to customer + supplier | F-INF-014 |
| 5 | Supplier | Order Management | New order alert → Accept → PROCESSING | F-SUP-017 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Payment decline | Order remains pending, stock released, customer notified | unknown |
| 3 | Event bus down | Order finalized but no downstream events; DLQ on recovery | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 1 | Cancel before payment | Cart restored, stock released | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/checkout.spec.ts` (if exists)
- Backend integration test: `tests/domains/orders/test_checkout.py` (if exists)
- Manual verification command: `pytest tests/domains/orders/test_checkout.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 2 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-002: Supplier payout

- **Features involved:** [F-ADM-024, F-ADM-049, F-INF-008, F-INF-009]
- **Actors involved:** [admin, supplier]
- **Domains involved:** [finance, suppliers]
- **Entry point:** Celery Beat payout_sweep
- **Exit state:** Batch approved, dispatched, supplier notified
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | System | Payout Sweep | Aggregate eligible payouts at 02:00 | F-SYS-001 |
| 2 | Admin | Payout Processing | Generate batch → Maker-checker → Approve | F-ADM-024 |
| 3 | System | Event Bus | payout.dispatched event emitted | F-INF-008 |
| 4 | Supplier | Payout Dashboard | View payout → Status updated | F-SUP-024 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Payment provider down | Batch fails, alert raised, retry next cycle | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 2 | Approval reversed | Batch marked failed, supplier notified | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/payout.spec.ts` (if exists)
- Backend integration test: `tests/domains/finance/test_payout.py` (if exists)
- Manual verification command: `pytest tests/domains/finance/test_payout.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 1 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-003: Return and refund

- **Features involved:** [F-CUST-013, F-CUST-014, F-ADM-011, F-ADM-052]
- **Actors involved:** [customer, admin, supplier]
- **Domains involved:** [orders, finance, suppliers]
- **Entry point:** POST /api/v1/customer/returns
- **Exit state:** Return approved, refund processed, inventory restored
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Customer | Return Request | Select items → Reason → Submit | F-CUST-013 |
| 2 | Admin | Returns Queue (RMA) | Review → Approve → Refund triggered | F-ADM-011 |
| 3 | Admin | Refund Management | Route via gateway → Ledger post | F-ADM-052 |
| 4 | Supplier | Returns Queue | Restock approved | F-SUP-029 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Return rejected | Customer notified, no refund, inventory unchanged | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 3 | Refund fails | Refund queued, alert to admin, retry | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/returns.spec.ts` (if exists)
- Backend integration test: `tests/domains/orders/test_returns.py` (if exists)
- Manual verification command: `pytest tests/domains/orders/test_returns.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 1 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-004: Logistics pickup and delivery

- **Features involved:** [F-LOG-011, F-LOG-012, F-LOG-013, F-LOG-015, F-INF-008]
- **Actors involved:** [supplier, logistics, customer]
- **Domains involved:** [logistics, orders]
- **Entry point:** QR Scan Handover at supplier warehouse
- **Exit state:** Parcel picked, in transit, delivered, proof captured
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Logistics | Shipment Queue | Claim PREPARED shipment | F-LOG-011 |
| 2 | Logistics | QR Scan Handover | Scan QR → PICKED FROM SUPPLIER | F-LOG-013 |
| 3 | Logistics | Transit Updates | LOGISTIC RECEIVED → OUT FOR DELIVERY | F-LOG-014 |
| 4 | Logistics | Delivery Confirmation | E-signature → DELIVERED → Settlement triggered | F-LOG-015 |
| 5 | System | Event Bus | shipment.delivered event emitted | F-INF-008 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | QR unreadable | Manual entry fallback, alert | unknown |
| 4 | Customer not available | DELAYED / RESCHEDULED | F-LOG-016 |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 4 | Wrong delivery | Return to supplier, status = FAILED | F-LOG-016 |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/logistics.spec.ts` (if exists)
- Backend integration test: `tests/domains/logistics/test_delivery.py` (if exists)
- Manual verification command: `pytest tests/domains/logistics/test_delivery.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 2 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-005: Admin ledger posting and reconciliation

- **Features involved:** [F-ADM-025, F-ADM-027, F-ADM-033, F-INF-008]
- **Actors involved:** [admin]
- **Domains involved:** [finance]
- **Entry point:** Admin creates journal entry
- **Exit state:** Journal posted, balanced, reconciled with bank
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Admin | Finance Hub | Open Chart of Accounts | F-ADM-025 |
| 2 | Admin | Journal Entries | Debit/credit lines → Balance check → Post | F-ADM-027 |
| 3 | System | Event Bus | journal.posted event emitted | F-INF-008 |
| 4 | Admin | Bank Reconciliation | Import CSV → Auto-match → Reconcile | F-ADM-033 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Unbalanced entry | Post rejected, error shown | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 2 | Post error | Reversal journal created | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/finance.spec.ts` (if exists)
- Backend integration test: `tests/domains/finance/test_journal.py` (if exists)
- Manual verification command: `pytest tests/domains/finance/test_journal.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 1 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-006: Customer registration and KYC

- **Features involved:** [F-CUST-001, F-INF-002, F-INF-004, F-INF-006]
- **Actors involved:** [customer]
- **Domains involved:** [customers, security]
- **Entry point:** POST /api/v1/customer/register
- **Exit state:** Customer registered, email verified, session established
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Customer | Customer Registration | Fill form → Submit | F-CUST-001 |
| 2 | System | Email Service | Verification email sent | F-INF-011 |
| 3 | Customer | Email Verification | Click link → Account activated | F-INF-002 |
| 4 | Customer | Customer Login | Email/password → Session established | F-CUST-002 |
| 5 | System | RBAC / Permissions | Default customer features granted | F-INF-006 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Email delivery fails | Registration pending, retry scheduled | unknown |
| 3 | Link expired | Resend verification email | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 1 | Duplicate email | Registration rejected, error shown | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/register.spec.ts` (if exists)
- Backend integration test: `tests/domains/customers/test_registration.py` (if exists)
- Manual verification command: `pytest tests/domains/customers/test_registration.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 2 required
- Rollback path: not_testable
- Verdict: BROKEN

## CHAIN-007: Supplier onboarding and first product listing

- **Features involved:** [F-SUP-001, F-SUP-003, F-SUP-006, F-ADM-013]
- **Actors involved:** [supplier, admin]
- **Domains involved:** [suppliers, catalog]
- **Entry point:** POST /api/v1/supplier/register
- **Exit state:** Supplier registered, KYC approved, first product live
- **Project completion critical:** yes

### Happy path
| Step | Actor | Feature | Expected outcome | Evidence |
|---|---|---|---|---|
| 1 | Supplier | Supplier Registration | Register → Role set | F-SUP-001 |
| 2 | Supplier | KYC Onboarding | Upload docs → Submit for review | F-SUP-003 |
| 3 | Admin | Supplier Management | Review KYC → Approve | F-ADM-013 |
| 4 | Supplier | Product Upload — Method 1 | Fill form → Upload image → Publish | F-SUP-006 |

### Failure paths
| Step | Failure mode | Expected behavior | Evidence |
|---|---|---|---|
| 2 | Docs rejected | Supplier notified, re-upload required | unknown |
| 3 | KYC incomplete | Supplier status remains pending | unknown |

### Rollback path
| Step | Trigger | Rollback action | Evidence |
|---|---|---|---|
| 3 | Approval reversed | Supplier status reverted to pending | unknown |

### Verification
- Playwright spec: `frontend/web_app/tests/e2e/supplier_onboarding.spec.ts` (if exists)
- Backend integration test: `tests/domains/suppliers/test_onboarding.py` (if exists)
- Manual verification command: `pytest tests/domains/suppliers/test_onboarding.py`

### Current status
- Happy path: not_testable (pre-flight failures)
- Failure paths: 0 covered / 2 required
- Rollback path: not_testable
- Verdict: BROKEN
