now we have to discuss the payment gateway integration.
we need a unified system which will easily attached with any payment gateway easily 

---------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------


Based on the forensic analysis of your codebase, I have excellent news: **You have already built 80% of this unified system.** 

Your backend already contains a brilliant **Payment Orchestrator Architecture** consisting of:
1. `BasePaymentGateway` (The abstract contract)
2. `PaymentGatewayRegistry` (The auto-discovery engine)
3. `PaymentEngine` (The central router)
4. `PaymentGatewayConnection` (The database model for credentials and fees)
5. Live Adapters for Stripe, Tap, Thawani, PayTabs, Mada, and STC Pay.

However, to make it truly **"Plug-and-Play"**—where a developer or admin can attach *any* new local gateway (e.g., JazzCash in Pakistan, Fawry in Egypt, or a new crypto processor) in under an hour without rewriting core logic—we need to standardize the missing 20%. 

Here is the **CTO-Level Master Plan** to finalize the **Zozi Universal Payment Connector**.

---

### 🏛️ Phase 1: The "Universal Adapter" Contract Standardization
To make adding a new gateway easy, every gateway must speak the exact same internal language. We must strictly enforce the `BasePaymentGateway` contract so that the `PaymentEngine` never needs to know *which* gateway it is talking to.

**The 5 Mandatory Methods Every Adapter Must Implement:**
1. **`authorize_and_capture()`**: Handles the actual charge. Must return a standardized `PaymentResult` (Success, Failed, or Requires_3DS/Redirect).
2. **`process_refund()`**: Handles full or partial refunds. Must return a `RefundResult`.
3. **`verify_webhook_signature()`**: The cryptographic security gate. Takes the raw HTTP body and headers, and returns `True/False`.
4. **`normalize_webhook_payload()`**: Translates the gateway's specific JSON (e.g., Stripe's `payment_intent.succeeded`) into Zozi’s internal `ZoziPaymentEvent` schema.
5. **`test_connection()`**: Pings the gateway's sandbox API to verify API keys are valid before the Admin enables it.

*Strategic Upgrade:* Create a **`GenericRESTAdapter`**. For simple gateways that don't have a Python SDK, the Admin can input the `Charge URL`, `Auth Headers`, and `JSON Payload Template` directly into the Admin UI. The `GenericRESTAdapter` uses these DB-stored templates to make the HTTP request, meaning **you can add basic gateways without writing any new Python code.**

---

### 🔄 Phase 2: The Universal Webhook Normalizer
The biggest headache in multi-gateway systems is that every provider sends webhooks in a completely different format. 

**The Plan:**
1. Create a single internal Pydantic model called `ZoziPaymentEvent`.
   * `zozi_order_id` (Extracted from metadata)
   * `gateway_transaction_id` (The provider's reference)
   * `status` (Enum: `PAID`, `FAILED`, `REFUNDED`, `CHARGEBACK`)
   * `amount_captured` (Decimal)
   * `gateway_fee_deducted` (Decimal)
2. **The Translation Layer:** Inside every adapter (e.g., `TapAdapter`, `StripeAdapter`), write a `translate_webhook()` function. 
3. **The Result:** The `PaymentEngine` and the `Treasury Ledger` *only* ever interact with `ZoziPaymentEvent`. If you add a new gateway tomorrow, the Treasury Engine doesn't need a single line of code changed, because the new adapter handles the translation.

---

### ⚙️ Phase 3: The Admin "Gateway Wizard" UI (No-Code Setup)
Your codebase already has the UI for managing `fee_percent`, `fixed_fee_amount`, and `settlement_cycle`. We need to expand this into a full "Gateway Onboarding Wizard" inside the Country Ledger.

**The 4-Step Admin Wizard:**
1. **Selection & Feasibility:** The Admin selects a country (e.g., Saudi Arabia). The system's *Algorithmic Heuristic Engine* suggests the best gateways (e.g., Tap, Mada, HyperPay) based on regional feasibility scores.
2. **Credential Vault:** The Admin inputs the `Public Key`, `Secret Key`, and `Webhook Secret`. 
   * *Security:* These are immediately encrypted via AES-256 (KMS) before being saved to the `PaymentGatewayConnection` table. They are never logged or returned to the frontend in plain text.
3. **Fee & Routing Rules:** The Admin defines:
   * *Who pays the fee?* (Toggle: `pass_fee_to_customer` or `absorb_by_supplier`).
   * *Routing Logic:* "If Cart > $500, route to Gateway A. If Cart < $500, route to Gateway B."
4. **The "Sandbox Test" Button:** The Admin clicks "Test Connection". The backend uses the `test_connection()` method to charge $1.00 to a test card and immediately refunds it. If successful, the "Enable for Checkout" toggle unlocks.

---

### 🛡️ Phase 4: Smart Routing & Fallback Engine (High Availability)
If Tap Payments goes down in Oman, checkout shouldn't fail. The Unified System must include an automatic fallback mechanism.

**The Plan:**
1. **Priority Tiers:** Allow the Admin to assign gateways to Tiers (Tier 1: Primary, Tier 2: Fallback).
2. **Health Monitoring:** The `PaymentEngine` tracks the success rate of every gateway over a rolling 1-hour window.
3. **Auto-Degradation:** If Tier 1's success rate drops below 85% (due to gateway downtime or bank network issues), the `PaymentEngine` automatically stops offering it at checkout and routes all traffic to Tier 2.
4. **Alerting:** The system fires an alert to the Command Center: *"⚠️ Thawani success rate dropped to 60%. Traffic automatically rerouted to Stripe."*

---

### 📝 Phase 5: The Developer Playbook (How to add a new gateway)
To ensure your engineering team can easily attach *any* gateway in the future, we will document a strict **4-Step Playbook**:

*   **Step 1: Create the File.** Create `backend/services/gateways/new_gateway.py`. Inherit from `BasePaymentGateway`.
*   **Step 2: Implement the 5 Methods.** Map the new gateway's API to `authorize_and_capture`, `process_refund`, `verify_webhook`, etc.
*   **Step 3: Auto-Discovery.** Because of your existing `PaymentGatewayRegistry` (which uses `pkgutil` to scan the folder), the new gateway is *automatically* registered the moment the server restarts. No manual imports required.
*   **Step 4: Admin Config.** Add the gateway's logo and setup instructions to the frontend `GatewayWizard` component.

---

### 🗺️ Execution Roadmap

| Phase | Action Item | Target Completion |
| :--- | :--- | :--- |
| **Week 1** | **Standardize Webhooks:** Build the `ZoziPaymentEvent` normalizer and update Stripe/Tap/Thawani adapters to use it. | High Priority |
| **Week 2** | **Security Hardening:** Implement AES-256 encryption for the `secret_key` and `webhook_secret` fields in the `PaymentGatewayConnection` DB model. | High Priority |
| **Week 3** | **Smart Routing:** Build the Health Monitor and Tier-based Fallback logic inside the `PaymentEngine`. | Medium Priority |
| **Week 4** | **The Generic REST Adapter:** Build the template-based adapter so Admins can connect simple REST-based gateways without developer intervention. | Low Priority (Future) |

### Summary
Your foundation (`PaymentEngine` + `Registry`) is already enterprise-grade. By enforcing the **Universal Webhook Normalizer**, adding **AES-256 Credential Encryption**, and building the **Smart Routing Fallback**, you will have a truly "Plug-and-Play" Payment Connector. You will be able to expand into new GCC or Asian markets and integrate their local payment gateways in days, not months.

**Shall we begin by designing the exact Pydantic schema for the `ZoziPaymentEvent` (The Universal Webhook Normalizer), or should we map out the AES-256 Encryption logic for the Admin Credential Vault first?**

---------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------


designing the exact Pydantic schema for the ZoziPaymentEvent (The Universal Webhook Normalizer) and map out the AES-256 Encryption logic for the Admin Credential Vault


---------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------


This is the definitive, CTO-level architectural blueprint for the **Universal Webhook Normalizer** and the **AES-256 Credential Vault**. 

By standardizing the internal event schema and cryptographically locking down gateway secrets, you decouple your core business logic from third-party API quirks and ensure that a database breach yields zero usable financial keys.

Here is the complete, code-free design and step-by-step implementation plan.

---

### 🏛️ PART 1: The `ZoziPaymentEvent` (Universal Webhook Normalizer)

#### 1. The Architectural Concept
Every payment gateway (Stripe, Tap, Thawani, PayTabs) sends webhooks in completely different formats, using different naming conventions and nested structures. If your Order Controller and Treasury Engine try to parse these individually, the codebase becomes a fragile, unmaintainable mess.

The `ZoziPaymentEvent` acts as a **Universal Translator**. 
1. The raw HTTP webhook hits the FastAPI router.
2. The specific Gateway Adapter (e.g., `TapAdapter`) verifies the cryptographic signature.
3. The Adapter translates the raw JSON into the strict `ZoziPaymentEvent` schema.
4. **From this point forward, the Zozi backend only interacts with the `ZoziPaymentEvent`.** The Order Controller and Treasury Ledger never need to know what "Tap" or "Stripe" JSON looks like.

#### 2. Schema Architecture (The Data Dictionary)
The schema must be strictly typed, using `Decimal` for all financial figures to prevent floating-point rounding errors in the Treasury Ledger.

| Field Category | Field Name | Data Type | Description & Purpose |
| :--- | :--- | :--- | :--- |
| **Metadata** | `provider_code` | String | e.g., "stripe", "tap", "thawani". |
| | `gateway_event_id` | String | The unique ID assigned by the gateway. Used for **Strict Idempotency** (preventing double-processing). |
| | `event_type` | Enum | Normalized internal event type (e.g., `PAYMENT_CAPTURED`, `REFUND_SUCCEEDED`, `CHARGEBACK_OPENED`). |
| | `environment` | Enum | `sandbox` or `live`. Prevents sandbox webhooks from triggering live order fulfillment. |
| | `timestamp` | DateTime | Exact time the event occurred at the gateway (UTC). |
| **Identifiers** | `zozi_order_id` | UUID/String | Extracted from the gateway's `metadata` field during checkout. Links the payment back to the Zozi DB. |
| | `gateway_transaction_id` | String | The gateway's internal reference (e.g., Stripe `pi_123`, Tap `ch_123`). |
| | `gateway_customer_id` | String | The tokenized customer ID at the gateway (for future recurring charges). |
| **Financials** | `gross_amount` | Decimal | The total amount charged to the customer. |
| | `currency` | String | ISO currency code (e.g., "SAR", "OMR"). |
| | `gateway_fee` | Decimal | **Crucial for Treasury:** The exact fee deducted by the gateway. Maps to GL `5010 Payment Gateway Fees`. |
| | `net_settlement` | Decimal | `gross_amount` minus `gateway_fee`. The exact amount that will hit the Zozi Bank Account. |
| **Risk & Fraud** | `fraud_score` | Integer | Gateway's internal risk score (0-100). |
| | `three_ds_status` | Enum | `passed`, `failed`, `attempted`, `not_required`. |
| | `avs_result` | Enum | Address Verification System match status. |
| **Forensics** | `raw_payload` | JSON | The exact, unmodified raw HTTP body. Stored for audit trails and dispute resolution. |

#### 3. Step-by-Step Implementation Plan

*   **Step 1: Define the Internal Enums & Contracts**
    *   Define the strict `ZoziEventStatus` enum. Map every gateway's specific statuses to this internal enum (e.g., Stripe's `payment_intent.succeeded` and Tap's `CHARGE_SUCCESS` both map to `ZoziEventStatus.PAYMENT_CAPTURED`).
*   **Step 2: Build the Adapter Translation Layer**
    *   Update the `BasePaymentGateway` abstract class. Add a mandatory `normalize_webhook(raw_body, headers) -> ZoziPaymentEvent` method.
    *   Force every adapter developer to write the mapping logic. If a gateway does not provide the `gateway_fee` in the webhook, the adapter must calculate it based on the `PaymentGatewayConnection` fee configuration stored in the DB.
*   **Step 3: Implement the Idempotency Gate**
    *   Before processing the `ZoziPaymentEvent`, the Webhook Router queries the `ProcessedWebhookEvent` table using the `gateway_event_id`. 
    *   If it exists, the router immediately returns HTTP 200 and halts. This prevents gateways from retrying and causing double-fulfillment.
*   **Step 4: Wire to the Treasury Engine**
    *   Create a dispatcher that listens for `ZoziPaymentEvent`.
    *   If `event_type == PAYMENT_CAPTURED`: Trigger the Treasury Service to Debit `1020 Gateway Clearing` and Credit `2060 Deferred Revenue`. Simultaneously, record the `gateway_fee` as an Expense.
*   **Step 5: Implement the "Ghost Order" Reconciliation**
    *   Build a nightly cron job that compares `Orders` marked as "Paid" against `ZoziPaymentEvents` received. If an order is marked paid but no `PAYMENT_CAPTURED` event exists in the normalized ledger, trigger a Critical Fraud Alert.

---

### 🏛️ PART 2: AES-256-GCM Admin Credential Vault

#### 1. The Architectural Concept
Payment gateway Secret Keys and Webhook Secrets are the "keys to the kingdom." If a hacker gains read-access to your PostgreSQL database, they must not be able to read these keys. 

We will implement **Transparent Application-Level Encryption** using **AES-256-GCM** (Galois/Counter Mode). GCM is mandatory because it provides both *confidentiality* (encryption) and *integrity* (tamper-evidence). If a rogue DBA tries to manually alter a ciphertext in the database, the decryption process will mathematically fail and throw an error, preventing the application from using a corrupted key.

#### 2. Cryptographic Architecture
*   **The Master Encryption Key (MEK):** A 256-bit key generated once. It is **never** stored in the database or committed to Git. It is injected into the FastAPI application at startup via a secure Environment Variable, AWS KMS, or HashiCorp Vault.
*   **The Nonce (IV):** A unique, random 12-byte initialization vector generated for *every single encryption operation*. Never reuse a nonce with the same MEK.
*   **The Authentication Tag:** A 16-byte cryptographic checksum generated by GCM to prove the data hasn't been tampered with.
*   **The Database Payload Structure:** The database column will store a single concatenated string formatted as: 
    `[Version Prefix]$[Base64 Nonce]$[Base64 Ciphertext]$[Base64 Auth Tag]`
    *(Example: `v1$a1b2c3...$x9y8z7...$f1g2h3...`)*. The version prefix allows for future key rotation.

#### 3. Step-by-Step Implementation Plan

*   **Step 1: Secure Key Injection & Initialization**
    *   Configure the FastAPI `settings.py` to load the `ZOZI_VAULT_MASTER_KEY` from the environment. 
    *   Implement a startup check: If the key is missing or not exactly 32 bytes (256 bits), the application must **refuse to boot**. This prevents the app from accidentally running in an unencrypted state.
*   **Step 2: Build the `VaultService` (The Cryptographic Engine)**
    *   Create a centralized service with two methods: `encrypt_secret(plaintext)` and `decrypt_secret(payload)`.
    *   **Encrypt Flow:** Generate random 12-byte Nonce $\rightarrow$ Initialize AES-256-GCM with MEK and Nonce $\rightarrow$ Encrypt Plaintext $\rightarrow$ Extract Ciphertext and Auth Tag $\rightarrow$ Concatenate and return the formatted string.
    *   **Decrypt Flow:** Split the string by `$` $\rightarrow$ Decode Base64 $\rightarrow$ Initialize GCM $\rightarrow$ Decrypt and Verify. If verification fails (tampering detected), throw a `CriticalSecurityException`.
*   **Step 3: Transparent SQLAlchemy Integration (TypeDecorator)**
    *   Do not force developers to manually call `VaultService.encrypt()` everywhere. 
    *   Create a custom SQLAlchemy `TypeDecorator` named `EncryptedString`. 
    *   Map the `secret_key` and `webhook_secret` columns in the `PaymentGatewayConnection` model to this custom type.
    *   *Result:* When the backend saves a new gateway config, SQLAlchemy automatically intercepts the plaintext, encrypts it, and saves the ciphertext. When the `PaymentEngine` reads the config to process a checkout, SQLAlchemy automatically decrypts it in memory. The business logic remains completely clean.
*   **Step 4: Memory Wiping & Zero-Logging**
    *   Ensure that the `raw_payload` of webhooks and the decrypted `secret_keys` are **never** written to application logs (e.g., standard `logger.info()`).
    *   Implement log-filtering middleware that uses Regex to detect and mask strings matching the patterns of Stripe (`sk_live_...`) or Tap (`sk_...`) keys before they hit the console or ELK stack.
*   **Step 5: The Key Rotation Strategy (Future-Proofing)**
    *   Because we included the `v1$` prefix in the database payload, we can support key rotation.
    *   If the MEK is compromised or needs routine rotation, inject a *new* MEK (`ZOZI_VAULT_MASTER_KEY_V2`).
    *   Update the `decrypt_secret` logic: If the payload starts with `v1$`, decrypt using the old MEK, immediately re-encrypt using the V2 MEK, and update the database row to `v2$`. This allows seamless, zero-downtime background rotation.

---

### 🛡️ Summary of the Security Posture

By implementing these two architectures, the Zozi Payment Orchestrator achieves **Enterprise Fintech Status**:

1.  **Normalization:** The business logic is entirely insulated from third-party API changes. If Tap Payments updates their webhook JSON structure next year, you only update the `TapAdapter` translation layer. The Order Controller, Treasury Ledger, and Customer Emails require **zero changes**.
2.  **Vaulting:** Even if an attacker executes a successful SQL Injection or steals a database backup, the `PaymentGatewayConnection` table yields only useless, mathematically locked ciphertext. Without the MEK (which resides in a separate, highly secured KMS/Vault environment), the attacker cannot issue refunds, steal funds, or spoof webhooks.

**Next Step:** 
map out the **Smart Routing & Fallback Engine** (how the system automatically switches from Tap to Stripe if Tap's API latency spikes), or should we design the **Admin "Gateway Onboarding Wizard" UI flow** for the Country Ledger.

---------------------------------------------------------------------------------------------------------
---------------------------------------------------------------------------------------------------------




# Payment Gateway Management

## Current Scope

The admin payment hub now supports two classes of providers:

- Live checkout adapters: `stripe`, `tap`, `paytabs`
- Managed provider templates: `paypal`, `hyperpay`, `omannet`, plus arbitrary custom providers

Every gateway record can store:

- Provider code and kind
- API/public/secret credentials
- Merchant identifier
- Base/test/webhook URLs
- Supported currencies
- Gateway fee and payout fee rules
- Whether fees are passed to the customer
- Settlement cycle: `daily`, `weekly`, or `monthly`
- Last test status and test message

## Checkout and Order Flow

- Checkout reads `/payments/methods` and renders fee-aware totals for the live adapters.
- Orders persist gateway fee snapshots on creation:
  - `payment_gateway_code`
  - `payment_gateway_fee_amount`
  - `payment_customer_total_amount`
  - `payment_gateway_fee_passed_to_customer`
- Stripe, Tap, and PayTabs charge the customer-payable total when the fee is configured to be passed through.

## Payout and Settlement Flow

- Finance quote preview uses the configured gateway fee profile.
- If `pass_fee_to_customer=false`, supplier payout estimates are reduced by the gateway fee.
- Supplier settlements now deduct the saved gateway fee allocation when the fee is not passed through.
- Settlement eligibility now respects the gateway record's `settlement_cycle`:
  - `daily` -> 1 day
  - `weekly` -> 7 days
  - `monthly` -> 30 days

## Provider Extension Path

To add the next real payment adapter:

1. Add provider defaults to `backend/controllers/payments_controller.py`
2. Add create/confirm/webhook or callback routes in `backend/routers/payments.py`
3. Wire checkout UI in `frontend/web_app/src/app/checkout/page.tsx`
4. Add gateway-management and order-flow tests under `backend/tests/`
5. Update this document with the new provider's runtime behavior

Managed templates can already store credentials and run sandbox connectivity checks, but they require provider-specific transaction logic before they can drive live checkout.