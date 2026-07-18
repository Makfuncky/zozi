## Payment Management System | Cash on Delivery | Pay by Card | Payout System of Supplier and Logistic Partner:

let's get back to cash management system of the ZOZI website.
There is 2 ways to payment "Cash on Delivery" and "Pay by Card"

- "Cash On Delivery" will receive by the Logistic Partner which is last end.
- "Pay by Card" will receive by the Zozi Management.

Now the point is how we will manage efficiently and track cash appropriately ?

Every Order have 4 components:
    1. Product Price.
    2. Delivery Charges. - which have 2 changes Pick-Up Charges and Drop-Off Charges. 
    3. VAT - 5% of the Product Price and Delivery Charges.
    4. ZOZI Service Charges - 10% to 20% of the Product Price.


## Problem 1: 
    When Logistic Partner receive cash on delivery from the customer then how Zozi Management will ask the Delivery Charges from the Logistic Partner and Logistic Partner never pay it back to the Zozi Management becasue it is their charges to keep with them.

## Problem 2: 
    How can we reconcile Management automatically and Payout System will work automatically for the Supplier and Logistic Partner based on the order completion and delivery.

## Problem 3:
    If the customer will order for Product A, B and C from Supplier A, B, and C.
    - `Supplier A` is located `City 1` and `Logistic Partner 1` will pick up the order from `City 1`.
    - `Supplier B` is located `City 2` and `Logistic Partner 2` will pick up the order from `City 2`.
    - `Supplier C` is located `City 3` and `Logistic Partner 3` will pick up the order from `City 3`.
    - Pick-up Charges of `City 1`, `City 2` and `City 3` 
    - Drop-off Charges of `City 4` which is customer location.
    - How it will be manage full process and how we will manage the reconciliation and payout system for the Supplier and Logistic Partner based on the order completion and delivery ?

## Problem 4:
    How we will manage the refund process for the customer and how it will be reflect to the Supplier and Logistic Partner based on the order cancellation and refund process ?

## Problem 5:
    How to reconcile with Bank System -> Supplier Payout -> Logistic Partner Payout -> Cash on Delivery Reconciliation -> Pay by Card Reconciliation -> Refund Reconciliation -> Payout Reconciliation -> etc.


What will be complete ecosystem of the payment management system for the ZOZI website and how it will be manage and track efficiently and automatically with the help of technology and how we will manage the reconciliation process for the Zozi Management, Supplier and Logistic Partner.


## April 6, 2026 — Current Operating Model And UI Ownership

The current product and finance surfaces now follow a strict ownership split so the payment cycle is easier to understand and operate.

### Admin UI Ownership
- `Admin -> Finance & Cash Management` explains the money lifecycle only.
- `Admin -> Finance -> Payouts` remains the batch execution and history workspace.
- `Admin -> Finance -> Bank Accounts` owns treasury setup, bank API connection testing, and supplier/logistics bank-account verification.
- `Admin -> Payments` owns checkout gateway configuration and provider onboarding, not treasury bank setup.

### Supplier And Logistics Profile Ownership
- `Supplier -> Profile -> Payout` now contains the supplier payout bank-account form and verification status.
- `Logistics Partner -> Profile -> Banking & Payouts` contains the logistics payout bank-account form and its verification status.
- Only verified recipient bank accounts are eligible for live payout dispatch.

### Card Payment Cycle
1. Customer pays online at checkout.
2. Zozi receives the collection into its payment rail and later into treasury.
3. Order delivery confirmation creates supplier and logistics settlement records.
4. Commission, VAT, refunds, and hold-window checks determine what is payable.
5. Finance processes eligible payouts.
6. Dispatch batches use the configured transfer provider and only verified bank accounts.
7. Bank transactions are reconciled back to payout records.

### Cash On Delivery Cycle
1. Customer pays the logistics partner on delivery.
2. Logistics keeps the delivery-side fee component defined by the settlement rules.
3. COD remittance due back to Zozi stays visible until treasury or bank reconciliation confirms receipt.
4. Supplier settlement remains pending until delivery, remittance visibility, and hold-window rules are satisfied.
5. Finance processes the supplier payout once eligible.
6. Bank reconciliation closes the COD remittance and payout outflow loop.

### Treasury Bank Account Responsibilities
- Store Zozi beneficiary, bank, IBAN, routing, and support contact details.
- Hold the reference prefix and treasury instructions used by finance operations.
- Support bank API connection testing through `POST /finance/admin/bank-settings/test-connection`.
- Expose readiness and missing requirements for the active payout provider before live dispatch.

### Recipient Bank Verification Responsibilities
- Supplier and logistics accounts enter an admin verification queue after create or update.
- Admin finance approves or rejects each account with an optional note.
- Rejected accounts stay editable from the supplier or logistics profile so corrected details can be resubmitted.
- Dispatch previews may show skipped rows when recipient banking is incomplete or unverified.


## April 4, 2026 — Implemented Bank Integration Layer

The current backend now includes a provider-ready payout dispatch layer that sits between Zozi finance workflows and a real bank or treasury API.

### What Is Implemented
- `manual_csv` remains the safe default provider for export-only payout instructions.
- `configured_bank_api` is now available as a direct-dispatch provider for supplier and logistics payouts.
- Finance admins can inspect available providers through `GET /finance/admin/transfer-providers`.
- Finance admins can dry-run or dispatch a payout batch through `POST /finance/admin/payouts/{kind}/dispatch` where `{kind}` is `supplier` or `logistics`.
- Live dispatch can also be queued as a tracked background job through `POST /finance/admin/payouts/{kind}/dispatch?background=true`.
- The admin finance dashboard now exposes transfer-provider selection, dry-run preview, and live dispatch queueing.
- Recipient validation is enforced before dispatch: only verified supplier/logistics bank accounts are considered dispatchable.
- Dry-run mode produces a dispatch manifest so finance can see which payouts are ready and which are skipped.
- Live dispatch mode uses an idempotency key and a provider response payload so bank submissions can be audited and reconciled later.
- The finance scheduler can now run a combined background cycle for payout processing, optional dispatch, and auto-reconciliation when the new finance scheduler flags are enabled.

### Current Runtime Settings
- `payout_transfer_provider`
- `bank_api_enabled`
- `bank_api_base_url`
- `bank_api_batch_path`
- `bank_api_auth_token`
- `bank_api_source_account_id`
- `bank_api_timeout_seconds`
- `finance_scheduler_process_payouts`
- `finance_scheduler_dispatch_payouts`
- `finance_scheduler_dispatch_dry_run`
- `finance_scheduler_dispatch_provider`

### What A Real Bank Sandbox Still Needs
- Real bank account details alone are not enough to enable live dispatch.
- Zozi still needs provider-issued sandbox credentials, the bank or treasury API base URL, the exact batch-submission path, the auth scheme or token, and source-account onboarding for the treasury account that will originate payouts.
- Production-grade reconciliation usually also needs bank webhooks or a statement export/import channel so provider confirmations can be matched automatically.

### Operational Model
1. Zozi computes supplier/logistics settlement eligibility from the existing ledger and settlement tables.
2. Finance verifies recipient bank accounts through the existing admin bank-account review workflow.
3. Finance runs a dry-run dispatch to inspect the manifest and skipped rows.
4. Finance reruns the same batch in live mode once the provider configuration is enabled.
5. Bank/provider responses are stored in the dispatch result so reconciliation can match real bank outflows against payout references.

### Scope Boundaries
- Direct dispatch currently applies to supplier payouts and logistics payouts.
- COD remittance is still an instruction/reconciliation flow, not a Zozi-initiated payout dispatch.
- Automated scheduling is now supported behind finance scheduler flags, but it should remain disabled until the sandbox or live provider rollout is validated.

### Recommended Production Rollout
1. Start with `manual_csv` in production and validate recipient bank-account hygiene.
2. Integrate one real treasury/bank endpoint behind `configured_bank_api` in sandbox mode.
3. Run dry-run dispatches in parallel with manual exports until manifests match expected payout batches.
4. Enable live bank dispatch for one payout rail at a time, starting with supplier payouts.
5. Enable the finance scheduler flags only after live dispatch is stable in sandbox and dry-run manifests consistently match finance expectations.
6. Add bank webhook or statement ingestion so payout confirmations reconcile without manual intervention.


----------------------------------------------------------------------------
----------------------------------------------------------------------------


Perfect, Muhammad — let’s architect the **complete Payment Management Ecosystem for Zozi** so it’s airtight, automated, and transparent for suppliers, logistics partners, and management.  

---

## 🔄 Core Payment Flow
Every order has **4 components**:  
1. **Product Price** → Supplier share (minus Zozi service charge).  
2. **Delivery Charges** → Split into Pick‑Up + Drop‑Off, retained by logistics partner.  
3. **VAT (5%)** → Applied on product + delivery, remitted to tax authority.  
4. **Zozi Service Charges (10–20%)** → Commission retained by Zozi.  

---

## ⚠️ Problem 1: COD & Delivery Charges
- **Solution**: Net Settlement  
  - Customer pays COD = Product Price + Delivery Charges + VAT.  
  - Logistics partner keeps **delivery charges** automatically.  
  - Logistics remits **Product Price + VAT** to Zozi.  
  - Zozi deducts service charge, pays supplier their net share.  
- **Control**: Each order tagged with breakdown → system auto‑splits amounts.  

---

## ⚠️ Problem 2: Automatic Reconciliation & Payouts
- **Solution**: Automated Ledger System  
  - Each order generates ledger entries:  
    - Customer payment → Zozi (Card) or Logistics (COD).  
    - Supplier payout → Pending until delivery confirmed.  
    - Logistics fee → Auto‑deducted.  
  - **Triggers**:  
    - Status = “Delivered & Confirmed” → Supplier payout scheduled.  
    - COD → Supplier payout only after Zozi receives remittance.  
- **Dashboards**:  
  - Supplier: Pending payouts, completed payouts, settlement dates.  
  - Logistics: COD collected, delivery fees retained, remittances made.  

---

## ⚠️ Problem 3: Multi‑Supplier, Multi‑City Orders
- **Scenario**: Customer orders A, B, C from suppliers in different cities.  
- **Solution**: Split Ledger by Supplier + Logistics Partner  
  - Each supplier tagged with their city.  
  - Each logistics partner tagged with pick‑up charges (City 1, 2, 3) + drop‑off charges (City 4).  
  - System auto‑allocates:  
    - Supplier A → Product Price – Zozi commission.  
    - Logistics Partner 1 → Pick‑up charge (City 1).  
    - Logistics Partner (Drop‑off City 4) → Drop‑off charge.  
  - Reconciliation engine matches COD/card receipts against multi‑supplier/multi‑logistics breakdown.  

---

## ⚠️ Problem 4: Refunds
- **Solution**: Reverse Ledger Entries  
  - Customer refund triggered → Payment gateway (Card) or Logistics (COD not yet remitted).  
  - Supplier payout reversed if already scheduled.  
  - Logistics fee refunded only if delivery not attempted.  
  - VAT adjusted automatically in refund ledger.  
- **Control**: Refund dashboard shows supplier/logistics impact per order.  

---

## ⚠️ Problem 5: Bank Reconciliation
- **Solution**: Unified Reconciliation Engine  
  - **Bank System Sync**: Daily import of bank statements.  
  - **Match Rules**:  
    - Supplier payouts → Match against supplier ledger.  
    - Logistics payouts → Match against logistics ledger.  
    - COD remittances → Match against logistics settlement reports.  
    - Card payments → Match against payment gateway reports.  
    - Refunds → Match against refund ledger.  
  - **Audit Trail**: Every transaction has order ID, supplier ID, logistics ID, settlement status.  

---

## 🏗️ Complete Ecosystem
1. **Order Ledger**: Auto‑generated per order (Product, Delivery, VAT, Zozi commission).  
2. **Payment Flow**: COD → Logistics net settlement; Card → Zozi merchant account.  
3. **Reconciliation Engine**: Matches COD, card, payouts, refunds daily.  
4. **Dashboards**:  
   - Zozi Management → Cashflow, pending settlements, VAT liability.  
   - Supplier → Net payouts, commission deducted, refund impact.  
   - Logistics → COD collected, fees retained, remittances.  
5. **Automation**: Payouts triggered by delivery confirmation, refunds reversed automatically.  
6. **Compliance**: VAT tracked per order, remitted monthly to authority.  

---

## 🎯 Investor‑Ready Narrative
- *“Zozi’s payment ecosystem is fully automated: COD net‑settled with logistics, card payments reconciled via gateway, supplier/logistics payouts triggered by delivery confirmation, and refunds reversed seamlessly. A unified reconciliation engine syncs with the bank daily, ensuring zero leakage, transparent cashflow, and investor confidence.”*  

---


------------------------------------------------------------------------------------
-------------------------------------------------------------------------------------

Here’s a **complete ecosystem design** for Zozi’s Payment Management System, with a flowchart and a detailed scenario table that includes reconciliation and banking integration. This is structured so you can drop it directly into your pitch deck.

---

## 🔄 Flowchart Diagram (Conceptual)

**Customer → Payment → Logistics/Zozi → Ledger → Reconciliation → Supplier/Logistics Payout → Refunds → Bank**

1. **Customer** places order (Product Price + Delivery Charges + VAT + Zozi Service Fee).  
2. **Payment**:  
   - COD → Collected by Logistics Partner.  
   - Card → Collected by Zozi Merchant Account.  
3. **Ledger Entry** auto‑created with all 4 components.  
4. **Reconciliation Engine**:  
   - Matches COD remittance reports from logistics.  
   - Matches card settlements from payment gateway.  
   - Syncs with bank account daily.  
5. **Supplier Payouts**: Triggered after delivery confirmation, net of Zozi commission.  
6. **Logistics Payouts**: Pick‑up + Drop‑off charges auto‑allocated, COD fees retained.  
7. **Refunds**: Reverse ledger entries, adjust supplier/logistics payouts, sync with bank.  
8. **Bank Integration**: Daily reconciliation of inflows (card, COD remittances) and outflows (supplier payouts, logistics payouts, refunds).

---

## 📊 Scenario Table — Payment, Reconciliation & Payouts

| Scenario | Payment Flow | Ledger Entry | Reconciliation | Supplier Payout | Logistics Payout | Bank Sync |
|----------|--------------|--------------|----------------|-----------------|------------------|-----------|
| COD Order (Single Supplier) | Customer → Logistics collects COD | Product Price, Delivery Fee, VAT, Zozi Fee | Logistics report vs Zozi ledger | Product Price – Zozi Fee → Supplier | Delivery Fee retained | COD remittance matched in bank |
| Card Order (Single Supplier) | Customer → Zozi Merchant Account | Product Price, Delivery Fee, VAT, Zozi Fee | Gateway report vs Zozi ledger | Product Price – Zozi Fee → Supplier | Delivery Fee → Logistics | Card settlement matched in bank |
| COD Order (Multi‑Supplier, Multi‑City) | Customer → Logistics collects COD | Split ledger per supplier & logistics partner | Logistics report vs Zozi ledger | Each supplier paid net share | Each logistics partner paid pick‑up + drop‑off | COD remittance matched in bank |
| Refund (Card Payment) | Zozi refunds via gateway | Reverse ledger entry | Gateway refund report vs Zozi ledger | Supplier payout reversed | Logistics fee refunded if not delivered | Refund matched in bank |
| Refund (COD Payment) | COD not remitted yet → Logistics returns cash | Reverse ledger entry | Logistics refund report vs Zozi ledger | Supplier payout reversed | Logistics fee refunded if not delivered | Refund matched in bank |
| VAT Settlement | VAT collected on product + delivery | VAT ledger entry | Monthly VAT reconciliation | N/A | N/A | VAT remittance matched in bank |
| Supplier Payout Cycle | Triggered after delivery confirmed | Supplier ledger entry | Bank transfer vs Zozi ledger | Supplier receives net payout | N/A | Supplier payout matched in bank |
| Logistics Payout Cycle | Triggered after delivery confirmed | Logistics ledger entry | Bank transfer vs Zozi ledger | N/A | Logistics partner receives payout | Logistics payout matched in bank |

---

## 🏗️ Automatic System Components

1. **Unified Ledger**: Every order generates a breakdown (Product, Delivery, VAT, Zozi Fee).  
2. **Reconciliation Engine**:  
   - COD → Logistics reports vs Zozi ledger vs bank deposits.  
   - Card → Gateway reports vs Zozi ledger vs bank deposits.  
   - Refunds → Reverse entries matched with bank outflows.  
3. **Bank Integration**: Daily sync of inflows/outflows with ledger.  
4. **Dashboards**:  
   - Zozi Management → Cashflow, VAT liability, pending settlements.  
   - Supplier → Net payouts, refunds, commissions.  
   - Logistics → COD collected, fees retained, remittances.  
5. **Automation**:  
   - Payouts triggered by delivery confirmation.  
   - Refunds reversed automatically.  
   - VAT tracked per order, remitted monthly.  

---

## 🎯 Investor‑Ready Narrative
- *“Zozi’s payment ecosystem is fintech‑grade: COD net‑settled with logistics, card payments reconciled via gateway, supplier/logistics payouts triggered automatically, refunds reversed seamlessly, and daily bank reconciliation ensures zero leakage. This creates transparency, efficiency, and investor confidence in cashflow management.”*

---



-----------------------------------------------------------------------------------
-----------------------------------------------------------------------------------


Here’s your **enhanced and detailed database table structure** for Zozi’s Payment Management System — fully aligned with the ER diagram I just delivered. This schema is designed for scalability, automation, and full reconciliation across COD, card payments, supplier payouts, logistics fees, refunds, and bank sync.

---

## 🗂️ Enhanced Database Tables

### 1. `customers`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| customer_id      | UUID (PK)  | Unique customer ID |
| name             | VARCHAR    | Full name |
| email            | VARCHAR    | Email address |
| phone            | VARCHAR    | Mobile number |
| city             | VARCHAR    | Location |
| created_at       | TIMESTAMP  | Account creation time |

---

### 2. `orders`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| order_id         | UUID (PK)  | Unique order ID |
| customer_id      | UUID (FK)  | Linked to customers |
| payment_method   | ENUM       | 'COD', 'CARD' |
| order_status     | ENUM       | 'Pending', 'Confirmed', 'Delivered', 'Cancelled', 'Refunded' |
| total_amount     | DECIMAL    | Final amount paid |
| vat_amount       | DECIMAL    | 5% VAT |
| zozi_service_fee | DECIMAL    | 10–20% of product price |
| created_at       | TIMESTAMP  | Order time |
| updated_at       | TIMESTAMP  | Last status update |

---

### 3. `order_items`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| item_id          | UUID (PK)  | Unique item ID |
| order_id         | UUID (FK)  | Linked to orders |
| supplier_id      | UUID (FK)  | Linked to suppliers |
| product_id       | UUID (FK)  | Linked to product catalog |
| product_price    | DECIMAL    | Price per item |
| zozi_fee         | DECIMAL    | Commission on item |
| vat_amount       | DECIMAL    | VAT on item |
| quantity         | INTEGER    | Quantity ordered |

---

### 4. `suppliers`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| supplier_id      | UUID (PK)  | Unique supplier ID |
| name             | VARCHAR    | Supplier name |
| city             | VARCHAR    | Location |
| email            | VARCHAR    | Contact email |
| bank_account     | VARCHAR    | IBAN or account number |

---

### 5. `logistics_partners`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| logistics_partner_id | UUID (PK) | Unique logistics ID |
| name             | VARCHAR    | Partner name |
| city             | VARCHAR    | Base city |
| contact_email    | VARCHAR    | Email |
| bank_account     | VARCHAR    | IBAN or account number |

---

### 6. `delivery_charges`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| delivery_id      | UUID (PK)  | Unique delivery ID |
| order_id         | UUID (FK)  | Linked to orders |
| pickup_city      | VARCHAR    | Supplier city |
| dropoff_city     | VARCHAR    | Customer city |
| pickup_charge    | DECIMAL    | Fee for pickup leg |
| dropoff_charge   | DECIMAL    | Fee for drop-off leg |
| logistics_partner_id | UUID (FK) | Linked to logistics partner |

---

### 7. `payments`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| payment_id       | UUID (PK)  | Unique payment ID |
| order_id         | UUID (FK)  | Linked to orders |
| method           | ENUM       | 'COD', 'CARD' |
| amount_received  | DECIMAL    | Total collected |
| received_by      | VARCHAR    | 'Zozi' or logistics partner |
| bank_transaction_id | VARCHAR | Linked to bank sync |
| payment_status   | ENUM       | 'Pending', 'Settled', 'Refunded' |
| settled_at       | TIMESTAMP  | Settlement time |

---

### 8. `supplier_payouts`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| payout_id        | UUID (PK)  | Unique payout ID |
| supplier_id      | UUID (FK)  | Linked to suppliers |
| order_id         | UUID (FK)  | Linked to orders |
| net_amount       | DECIMAL    | Product price – Zozi fee |
| payout_status    | ENUM       | 'Pending', 'Paid', 'Reversed' |
| paid_at          | TIMESTAMP  | Payout time |
| bank_transaction_id | VARCHAR | Linked to bank sync |

---

### 9. `logistics_payouts`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| payout_id        | UUID (PK)  | Unique payout ID |
| logistics_partner_id | UUID (FK) | Linked to logistics partner |
| order_id         | UUID (FK)  | Linked to orders |
| pickup_charge    | DECIMAL    | Pickup fee |
| dropoff_charge   | DECIMAL    | Drop-off fee |
| cod_fee          | DECIMAL    | COD handling fee |
| payout_status    | ENUM       | 'Pending', 'Paid', 'Reversed' |
| paid_at          | TIMESTAMP  | Payout time |
| bank_transaction_id | VARCHAR | Linked to bank sync |

---

### 10. `refunds`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| refund_id        | UUID (PK)  | Unique refund ID |
| order_id         | UUID (FK)  | Linked to orders |
| reason           | TEXT       | Reason for refund |
| refund_amount    | DECIMAL    | Amount refunded |
| refund_method    | ENUM       | 'CARD', 'COD' |
| refund_status    | ENUM       | 'Pending', 'Processed' |
| processed_at     | TIMESTAMP  | Refund time |
| bank_transaction_id | VARCHAR | Linked to bank sync |

---

### 11. `bank_transactions`
| Column Name       | Type       | Description |
|------------------|------------|-------------|
| transaction_id   | VARCHAR (PK) | Bank reference ID |
| source           | VARCHAR    | 'Zozi', 'Logistics', 'Gateway' |
| type             | ENUM       | 'Inflow', 'Outflow' |
| amount           | DECIMAL    | Transaction amount |
| linked_entity    | UUID       | Supplier, logistics, or refund ID |
| reconciled       | BOOLEAN    | True/False |
| reconciled_at    | TIMESTAMP  | Reconciliation time |

---
