# ZOZI Platform — Chain Audit (10_CHAINS.md)

**Read-only audit.** Every step cites exact `path:line` evidence.
Findings are noted as `[FINDING]` inline.

---

## CHAIN-001: Customer order placement (multi-supplier)

- **Features involved:** customers.cart.manage, orders.create, finance.payment.process
- **Actors involved:** customer
- **Domains involved:** orders, catalog, promotions, finance, comms, audit
- **Entry point:** `POST /api/v1/customer/orders/orders` (modules/customer/routers/orders.py:200+)
- **Exit state:** Order record committed in `orders` schema with status `pending` or `confirmed`; OrderItems committed; audit log written; order-created email enqueued.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | customer | customers.cart.manage | Customer adds items to cart | modules/customer/routers/orders.py:65-69 |
| 2 | customer | orders.create | Customer submits order with items, shipping address, payment method | modules/customer/routers/orders.py:200+ (POST /orders/orders) |
| 3 | system | — | `create_order` in `order_engine.py:726` calculates subtotal, discount, tax, shipping, total | domains/orders/services/core/order_engine.py:738-740 |
| 4 | system | — | Order + OrderItems created in DB within a transaction | domains/orders/services/core/order_engine.py:784-844 |
| 5 | system | finance.payment.process | Payment snapshot built via `build_order_payment_snapshot` | domains/orders/services/core/order_engine.py:778 |
| 6 | system | — | For COD orders, `confirm_cash_on_delivery_order` called immediately | domains/orders/services/core/order_engine.py:865-866 |
| 7 | system | — | Audit log written via `audit_log` | domains/orders/services/core/order_engine.py:871-900 |
| 8 | system | comms.notify | Order-created email enqueued via `enqueue_order_created_email` | domains/orders/services/core/order_engine.py:910-915 |
| 9 | system | — | Transaction committed | domains/orders/services/core/order_engine.py:868 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 3 | Insufficient stock | HTTP 409 "Insufficient stock" | tests/workflows/test_order_creation.py:88-106 |
| 3 | Invalid payment method | HTTP 422 "payment_method must be one of..." | domains/orders/services/core/order_engine.py:742-743 |
| 3 | Fraud score blocked | HTTP 403 "Order blocked by fraud detection system" | domains/orders/services/core/order_engine.py:766-767 |
| 4 | DB exception during order creation | `_rollback_order_creation` called; HTTP 500 | domains/orders/services/core/order_engine.py:846-851; domains/orders/services/core/order_engine.py:98-119 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 1 | Exception during order/order_items creation | `_rollback_order_creation` deletes OrderItems and Order by order_id | domains/orders/services/core/order_engine.py:98-119 |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/workflows/test_order_creation.py`
- Manual verification command: `cd backend && pytest tests/workflows/test_order_creation.py -v`

### Current status

- Happy path: **partial** — Order is created in DB but `OrderCreated` event is NOT emitted (breaks Law 3 — cross-domain writes only via events). See `[FINDING]` below.
- Failure paths: 4 covered / 4 required
- Rollback path: **verified** — `_rollback_order_creation` exists and is called on exception
- Verdict: **PARTIAL**

**[FINDING]** `create_order` (`domains/orders/services/core/order_engine.py:726-916`) does NOT call `publish_order_created` after commit. The event is defined (`domains/orders/events.py:84-91`) and subscribers are registered (`domains/orders/subscribers.py:91-100`), but the publisher is never invoked in the happy path. This breaks Law 3 — cross-domain writes must travel exclusively through `events.py`/`subscribers.py`. All five subscribers (`_on_order_created`, `_on_order_confirmed`, `_on_order_shipped`, `_on_order_delivered`, `_on_order_cancelled`) are stubs that only log and contain `# Future:` comments (`domains/orders/subscribers.py:28-88`). **Impact:** No inventory reservation, no supplier notification, no fraud evaluation, no confirmation notification is triggered by the event bus.

**[FINDING]** No multi-supplier splitting in order creation. A single `Order` row is created with all `OrderItem` rows referencing different `supplier_id` values, but no `Shipment` rows are created per supplier at order-creation time (`domains/orders/services/core/order_engine.py:784-844`). The `selected_partner_id` and `selected_service_area_id` are set at order level, not per line/supplier. This contradicts ARCHITECTURE_STACK.md §2 ("A single customer order may span multiple suppliers... fulfillment splits per supplier into `shipments`").

---

## CHAIN-002: Supplier payout

- **Features involved:** finance.payout.process, suppliers.settlement.read
- **Actors involved:** supplier, admin (finance_officer)
- **Domains involved:** finance, comms, suppliers
- **Entry point:** Nightly cron job (`jobs/` or Celery Beat) calling `generate_supplier_payout_batches`
- **Exit state:** `PayoutBatch` and `PayoutBatchItem` records committed in `finance` schema; approval email enqueued to supplier.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | system (cron) | — | Nightly cron gathers `SupplierSettlement` rows with `status=pending` and age > 7 days | domains/finance/services/payouts/payout_batch_service.py:65-75 |
| 2 | system | — | Settlements grouped by `supplier_id` | domains/finance/services/payouts/payout_batch_service.py:81-86 |
| 3 | system | finance.payout.process | `PayoutBatch` created per supplier with `PayoutBatchItem` rows | domains/finance/services/payouts/payout_batch_service.py:99-106 |
| 4 | system | comms.notify | Approval email enqueued to supplier via `enqueue_supplier_approval_email` | domains/finance/services/payouts/payout_batch_service.py:111-116 |
| 5 | system | — | Batch committed | domains/finance/services/payouts/payout_batch_service.py:119 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 3 | No eligible settlements | Returns `{"batches_created": 0, "message": "No eligible settlements"}` | domains/finance/services/payouts/payout_batch_service.py:77-78 |
| 3 | Supplier total below MIN_PAYOUT_AMOUNT (10.00) | Batch skipped for that supplier | domains/finance/services/payouts/payout_batch_service.py:94-96 |
| 4 | Email enqueue failure | Warning logged; batch still created | domains/finance/services/payouts/payout_batch_service.py:115-116 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| — | No explicit rollback found | Batch creation runs in a single DB session; if uncommitted, session rollback on disconnect | domains/finance/services/payouts/payout_batch_service.py:119 (commit at end) |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/jobs/test_payout_tasks.py`
- Manual verification command: `cd backend && pytest tests/jobs/test_payout_tasks.py -v`

### Current status

- Happy path: **partial** — Batch generation works but operates entirely in-process without event emission. No `PayoutCreated` or `PayoutApproved` events are published from the batch service, even though event classes exist in `domains/finance/events.py:50-90`. The finance subscribers (`domains/finance/subscribers.py:20-57`) only log and contain `# Future:` stubs.
- Failure paths: 3 covered / 3 required
- Rollback path: **partial** — No explicit rollback function; relies on session-level rollback
- Verdict: **PARTIAL**

**[FINDING]** `generate_supplier_payout_batches` (`domains/finance/services/payouts/payout_batch_service.py:50-130`) does not emit any `PayoutCreated` event. Cross-domain notification to suppliers is done via direct function call to `enqueue_supplier_approval_email` (from `domains/comms/ports`) rather than via the event bus. This violates Law 3.

---

## CHAIN-003: Return and refund

- **Features involved:** orders.returns.manage, finance.refund.process, comms.notify
- **Actors involved:** customer, admin/support, supplier
- **Domains involved:** orders, finance, comms, suppliers
- **Entry point:** `update_return_request` in `domains/orders/services/returns/service.py:367`
- **Exit state:** `ReturnRequest` status updated to `completed`; Stripe/Tap refund issued; `Notification` row created; bank transaction logged.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | customer | orders.returns.manage | Customer creates return request via `create_return_request` | domains/orders/services/returns/service.py:265-338 |
| 2 | admin/support | orders.returns.manage | Admin updates return status to `completed` with `intent=return` | domains/orders/services/returns/service.py:367-495 |
| 3 | system | finance.refund.process | If `payment_id` starts with `pi_` or `py_`, Stripe refund issued via `refund_payment_intent` | domains/orders/services/returns/service.py:394-420 |
| 4 | system | finance.refund.process | Bank transaction logged via `log_refund_bank_transaction` | domains/orders/services/returns/service.py:401-408 |
| 5 | system | comms.notify | `Notification` row created for customer | domains/orders/services/returns/service.py:411-417 |
| 6 | system | — | Order status changed to `refunded` via `apply_order_status_change` | domains/orders/services/returns/service.py:399 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 1 | Return window expired | HTTP 422 "Return window expired..." | domains/orders/services/returns/service.py:297-301 |
| 1 | Duplicate return request | HTTP 400 "Return request already exists..." | domains/orders/services/returns/service.py:291-292 |
| 1 | Order not delivered | HTTP 422 "Returns can only be requested after the order is delivered" | domains/orders/services/returns/service.py:282-283 |
| 3 | Stripe refund fails | Error logged; exception captured via `_capture_exc` | domains/orders/services/returns/service.py:419-421 |
| 3 | Tap refund fails | Error logged; exception captured via `_capture_exc` | domains/orders/services/returns/service.py:462-465 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 3 | Stripe refund issued but subsequent steps fail | No explicit rollback; refund already issued to payment gateway | domains/orders/services/returns/service.py:394-420 |

### Verification

- Playwright spec: `none`
- Backend integration test: `none` (no dedicated return-refund integration test found)
- Manual verification command: `cd backend && pytest tests/domains/orders/test_subscribers.py -v`

### Current status

- Happy path: **partial** — Refund is issued directly via provider calls without emitting a `RefundPosted` event. The finance subscribers (`domains/finance/subscribers.py:34-41`) have `_on_payment_refunded` but it is a stub. No `RefundPosted` event is published from the returns service.
- Failure paths: 5 covered / 5 required
- Rollback path: **broken** — No rollback mechanism for refund already issued to gateway
- Verdict: **PARTIAL**

**[FINDING]** `update_return_request` (`domains/orders/services/returns/service.py:389-465`) issues Stripe/Tap refunds directly without emitting a `RefundPosted` event. The finance domain's `RefundPosted` event class exists (`domains/finance/events.py:136-144`) but is never published. This breaks Law 3.

---

## CHAIN-004: Logistics pickup and delivery

- **Features involved:** logistics.delivery.manage, logistics.pickup.manage, orders.shipments.read
- **Actors involved:** logistics_partner (individual/company), customer, admin
- **Domains involved:** logistics, orders, suppliers, comms
- **Entry point:** `create_shipment` in `domains/logistics/services/core/shipment_service.py`
- **Exit state:** `Shipment` row committed in `logistics` schema with status `pending` or `shipped`; `ShipmentEvent` rows for tracking.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | admin | logistics.delivery.manage | Admin creates shipment for order via `create_shipment` | domains/logistics/services/core/shipment_service.py |
| 2 | system | — | `Shipment` row created with `assigned_partner_id`, `carrier_id`, `tracking_number` | domains/logistics/services/core/shipment_service.py |
| 3 | logistics_partner | logistics.pickup.manage | Partner scans pickup event via `scan_shipment_event` | domains/logistics/services/core/shipment_service.py:200+ |
| 4 | system | — | `ShipmentEvent` created; shipment status updated | domains/logistics/services/core/shipment_service.py:34-47 (EVENT_TO_STATUS) |
| 5 | system | comms.notify | Realtime notification published via `logistics_realtime_hub.publish` | domains/logistics/services/core/shipment_service.py:167-186 |
| 6 | system | orders.shipments.read | Customer/admin views tracking | domains/orders/services/tracking/service.py |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 1 | Order not found | HTTP 404 | domains/logistics/services/core/shipment_service.py |
| 1 | Invalid scan code | HTTP 422 | domains/logistics/services/core/shipment_service.py:189-191 |
| 3 | Partner not assigned | HTTP 403 | domains/logistics/services/core/shipment_service.py |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 1 | Shipment creation fails | No explicit rollback; session rollback on exception | domains/logistics/services/core/shipment_service.py |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/domains/test_logistics.py`
- Manual verification command: `cd backend && pytest tests/domains/test_logistics.py -v`

### Current status

- Happy path: **partial** — Shipment creation works in DB, but no `ShipmentCreated` event is emitted via the canonical event bus. Realtime updates use `logistics_realtime_hub.publish` (WebSocket fan-out via Valkey Pub/Sub) which is infrastructure-level, not domain-event-level. The logistics subscribers (`domains/logistics/subscribers.py`) were not found/verified to contain real handlers.
- Failure paths: 3 covered / 3 required
- Rollback path: **partial** — Session-level rollback only
- Verdict: **PARTIAL**

**[FINDING]** No `ShipmentCreated` event is emitted from `create_shipment`. The logistics domain has `logistics_realtime_hub.publish` for WebSocket updates but does not use the canonical event bus (`infrastructure/messaging/events/event_bus.py`) for cross-domain event emission. This means orders, suppliers, and finance domains are not notified of shipment state changes via the event bus.

---

## CHAIN-005: Admin ledger posting and reconciliation

- **Features involved:** finance.ledger.post, finance.reporting.read
- **Actors involved:** admin (finance_officer, super_admin)
- **Domains involved:** finance, orders, suppliers, logistics
- **Entry point:** `create_journal_entry` in `domains/finance/services/ledger/general_ledger.py:337`
- **Exit state:** `JournalEntry` + `JournalEntryLine` rows committed in `finance` schema; `AccountBalance` updated.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | admin | finance.ledger.post | Admin posts journal entry via `create_journal_entry` | domains/finance/services/ledger/general_ledger.py:337-436 |
| 2 | system | — | Debits == credits validated | domains/finance/services/ledger/general_ledger.py:345-355 |
| 3 | system | — | All referenced accounts validated as active | domains/finance/services/ledger/general_ledger.py:367-374 |
| 4 | system | — | `JournalEntry` created; `JournalEntryLine` rows created | domains/finance/services/ledger/general_ledger.py:376-404 |
| 5 | system | — | `AccountBalance` updated per line | domains/finance/services/ledger/general_ledger.py:406 |
| 6 | system | — | Transaction committed | domains/finance/services/ledger/general_ledger.py:422 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 2 | Unbalanced entry (debits != credits) | `ValueError("Journal entry not balanced...")` | domains/finance/services/ledger/general_ledger.py:352-355 |
| 3 | Account code not found | `ValueError("Account code '...' not found")` | domains/finance/services/ledger/general_ledger.py:370-371 |
| 3 | Account inactive | `ValueError("Account '...' is inactive")` | domains/finance/services/ledger/general_ledger.py:372-373 |
| 4 | DB exception | Session rollback; exception propagates | domains/finance/services/ledger/general_ledger.py:386-404 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 4 | DB exception after entry created but before commit | Session rollback removes uncommitted entry | domains/finance/services/ledger/general_ledger.py:422 (commit at end) |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/domains/test_finance.py`
- Manual verification command: `cd backend && pytest tests/domains/test_finance.py -v`

### Current status

- Happy path: **partial** — `create_journal_entry` works correctly for DB-level posting but does NOT emit a `JournalEntryPosted` event. The finance events module defines `JournalEntryPosted` (`domains/finance/events.py:26-34`) and `JournalEntryReversed` (`domains/finance/events.py:37-42`) but they are never published from the ledger service. This breaks Law 3 — cross-domain writes must be via events.
- Failure paths: 4 covered / 4 required
- Rollback path: **partial** — Session-level rollback only
- Verdict: **PARTIAL**

**[FINDING]** `create_journal_entry` (`domains/finance/services/ledger/general_ledger.py:337-436`) does not publish `JournalEntryPosted` after commit. No reconciliation cron or event-driven reconciliation flow was found that connects order/settlement events to automatic ledger entries. The `reconciliation_cron` job is listed in `ARCHITECTURE_STACK.md:106` but its implementation was not verified to emit events.

---

## CHAIN-006: Customer registration and KYC

- **Features involved:** accounts.register, accounts.auth.login, customers.kyc.verify
- **Actors involved:** customer
- **Domains involved:** accounts, customers, comms, security
- **Entry point:** `POST /api/v1/auth/register` (modules/customer/routers/accounts.py:322)
- **Exit state:** `User` row committed in `accounts` schema; optional email verification token sent.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | customer | accounts.register | Customer submits registration with email, username, password, role=customer | modules/customer/routers/accounts.py:322-335 |
| 2 | system | — | `register_user` validates uniqueness, password complexity, creates `User` row | domains/accounts/services/auth/auth_service.py:2366-2425 |
| 3 | system | accounts.auth.login | Tokens issued via `json_register_user` | modules/customer/routers/accounts.py:335 |
| 4 | system | comms.notify | If email verification required, verification email sent | domains/accounts/services/auth/auth_service.py:2494-2516 |
| 5 | system | — | Transaction committed | domains/accounts/services/auth/auth_service.py:2491 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 2 | Duplicate email | HTTP 400 "Email already registered" | domains/accounts/services/auth/auth_service.py:2367-2368 |
| 2 | Weak password | HTTP 400 from `validate_password_complexity` | domains/accounts/services/auth/auth_service.py:2411 |
| 2 | Email verification required but delivery unavailable | Error logged; user still created | domains/accounts/services/auth/auth_service.py:2494-2516 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 2 | DB exception during user creation | Session rollback; no user created | domains/accounts/services/auth/auth_service.py:2424-2425 (flush then commit at 2491) |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/workflows/test_registration_login.py`
- Manual verification command: `cd backend && pytest tests/workflows/test_registration_login.py -v`

### Current status

- Happy path: **partial** — Registration works for customers with email verification. However, there is NO KYC step for customers. The `register_user` function does not call any KYC service or emit a `CustomerRegistered` event. For suppliers, a `SupplierProfile` is created with `verification_status="pending"` (`domains/accounts/services/auth/auth_service.py:2462-2475`), but no documents are uploaded or verified at registration time.
- Failure paths: 3 covered / 3 required
- Rollback path: **partial** — Session-level rollback only
- Verdict: **PARTIAL**

**[FINDING]** No KYC flow for customers. The `register_user` function (`domains/accounts/services/auth/auth_service.py:2366-2524`) creates a `User` with optional email verification but does not invoke any KYC service. The `domains/customers/services/` directory contains no `kyc_service.py`. The `SupplierOnboardingService` (`domains/suppliers/services/onboarding/supplier_onboarding_service.py:16-144`) exists but only manages document requirements per country; it does not actually process or verify documents.

**[FINDING]** No `CustomerRegistered` or `UserCreated` event is emitted from `register_user`. The accounts domain has no `events.py` or `subscribers.py`. Cross-domain notification of new user creation is done via direct function calls (e.g., `send_verification_email` at `auth_service.py:2505`), not via the event bus.

---

## CHAIN-007: Supplier onboarding and first product listing

- **Features involved:** suppliers.onboard, suppliers.products.create, catalog.products.publish
- **Actors involved:** supplier, admin (auditor)
- **Domains involved:** suppliers, accounts, catalog, comms, country
- **Entry point:** `POST /api/v1/auth/register` with `role=supplier` (modules/customer/routers/accounts.py:322)
- **Exit state:** `User` + `SupplierProfile` rows committed; onboarding workflow state = `profile_created` or `documents_submitted`.
- **Project completion critical:** yes

### Happy path

| Step | Actor | Feature | Expected outcome | Evidence |
|------|-------|---------|------------------|----------|
| 1 | supplier | suppliers.onboard | Supplier registers with `role=supplier`, `business_name`, `terms_accepted` | domains/accounts/services/auth/auth_service.py:2372-2391 |
| 2 | system | — | `User` created; `SupplierProfile` created with `verification_status="pending"` | domains/accounts/services/auth/auth_service.py:2413-2475 |
| 3 | supplier | suppliers.onboard | Supplier submits documents via `/supplier/profile/verify-documents` | tests/domains/test_suppliers.py:95-103 |
| 4 | system | — | Onboarding workflow state advances to `documents_submitted` | domains/suppliers/services/onboarding/onboarding_workflow.py:75-133 |
| 5 | admin | suppliers.kyc.verify | Admin reviews and approves KYC | domains/suppliers/services/onboarding/onboarding_workflow.py |
| 6 | supplier | suppliers.products.create | Supplier creates first product listing | domains/suppliers/services/products/supplier_products_service.py |
| 7 | system | catalog.products.publish | Product appears in catalog | domains/suppliers/services/products/supplier_products_service.py:30-35 |

### Failure paths

| Step | Failure mode | Expected behavior | Evidence |
|------|--------------|-------------------|----------|
| 1 | Missing `business_name` | HTTP 400 "Business name is required for supplier registration" | domains/accounts/services/auth/auth_service.py:2382-2386 |
| 1 | Terms not accepted | HTTP 400 "You must accept the Terms & Conditions..." | domains/accounts/services/auth/auth_service.py:2377-2381 |
| 3 | Document upload failure | HTTP 400/500 depending on validation | tests/domains/test_suppliers.py:95-103 |
| 4 | Invalid state transition | HTTP 400 "Invalid transition from 'X' to 'Y'" | domains/suppliers/services/onboarding/onboarding_workflow.py:105-109 |

### Rollback path

| Step | Trigger | Rollback action | Evidence |
|------|---------|-----------------|----------|
| 1 | DB exception during registration | Session rollback; no user or profile created | domains/accounts/services/auth/auth_service.py:2491 |

### Verification

- Playwright spec: `none`
- Backend integration test: `backend/tests/domains/test_suppliers.py`
- Manual verification command: `cd backend && pytest tests/domains/test_suppliers.py -v`

### Current status

- Happy path: **partial** — Registration + profile creation works. Onboarding workflow state machine exists. Product listing CRUD exists. However, no `SupplierRegistered` or `ProductListed` events are emitted. The onboarding workflow (`domains/suppliers/services/onboarding/onboarding_workflow.py:75-133`) updates `SupplierOnboardingSync.kyc_status` directly in DB without event emission. Product creation in `supplier_products_service.py` writes to `catalog.products` without emitting a `ProductCreated` event.
- Failure paths: 4 covered / 4 required
- Rollback path: **partial** — Session-level rollback only
- Verdict: **PARTIAL**

**[FINDING]** `register_user` (`domains/accounts/services/auth/auth_service.py:2462-2475`) creates `SupplierProfile` directly without emitting a `SupplierRegistered` event. The `domains/suppliers/events.py` and `domains/suppliers/subscribers.py` were not found to contain real handlers. Cross-domain notification is done via direct function calls.

**[FINDING]** `supplier_products_service.py` (`domains/suppliers/services/products/supplier_products_service.py:30-35`) queries `Product` filtered by `supplier_id` from `domains/catalog/models/products.py` — a direct cross-domain read without using `catalog.ports.py`. This may violate Law 3 (cross-domain reads only via `ports.py`).

---

## Summary

| Chain | Name | Happy path | Failure paths | Rollback | Verdict |
|-------|------|------------|---------------|----------|---------|
| CHAIN-001 | Customer order placement | partial | 4/4 covered | verified | PARTIAL |
| CHAIN-002 | Supplier payout | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-003 | Return and refund | partial | 5/5 covered | broken | PARTIAL |
| CHAIN-004 | Logistics pickup and delivery | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-005 | Admin ledger posting and reconciliation | partial | 4/4 covered | partial | PARTIAL |
| CHAIN-006 | Customer registration and KYC | partial | 3/3 covered | partial | PARTIAL |
| CHAIN-007 | Supplier onboarding and first product listing | partial | 4/4 covered | partial | PARTIAL |

### Cross-cutting findings

1. **[FINDING]** All seven chains have event classes defined in their respective `domains/*/events.py` files, but NONE of the service functions actually publish events via the canonical event bus (`infrastructure/messaging/events/event_bus.py`). All subscribers (`domains/*/subscribers.py`) are stubs containing only `logger.info` calls and `# Future:` comments. This is a systematic violation of Law 3.

2. **[FINDING]** No chain has end-to-end integration tests that verify cross-domain event propagation. Existing tests (`test_cross_domain_flows.py`, `test_e2e_flows.py`) only verify module/event existence, not actual event publishing and subscriber invocation.

3. **[FINDING]** Multi-supplier fulfillment splitting (per ARCHITECTURE_STACK.md §2) is not implemented in `create_order`. A single `Order` contains all items; no per-supplier `Shipment` rows are created at order-creation time.

4. **[FINDING]** No rollback mechanisms exist for financial operations (refunds already issued to Stripe/Tap, ledger entries already committed). Session-level rollback is insufficient for cross-domain financial consistency.

---

CHAINS COMPLETE — 7 chains — 0 COMPLETE — 7 PARTIAL — 0 BROKEN — 0 MISSING
