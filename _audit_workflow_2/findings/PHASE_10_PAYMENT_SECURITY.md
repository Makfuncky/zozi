# PHASE 10 — PAYMENT SYSTEM FORENSIC AND SECURITY AUDIT

**Project:** ZOZI Marketplace E-Commerce Platform  
**Path:** `D:\Projects\10- E-COMMERCE WEBSITE\zozi`  
**Date:** 2026-09-11  
**Auditor:** Kilo (forensic static analysis)  
**Scope:** Payment providers, integrations, initialization, sessions, callbacks, webhooks, verification, signatures, transaction IDs, order/payment relationship, refunds, partial refunds, failed payments, retries, duplicate callbacks, idempotency, currency handling, amount calculation, discounts, taxes, shipping charges, payment status transitions, secrets, API credentials, frontend payment handling  

---

## 1. PAYMENT PROVIDERS AND INTEGRATIONS IDENTIFIED

### 1.1 Active Payment Providers (VERIFIED)

| Provider | Code | Integration Type | Status |
|----------|------|------------------|--------|
| Stripe | `stripe` | Native SDK (`stripe_sdk.py`) + Checkout Session + Payment Intents | VERIFIED |
| Tap Payments | `tap` | HTTP REST API (`gateway_tap.py`, `providers/payments/tap.py`) | VERIFIED |
| PayTabs | `paytabs` | HTTP REST API (`gateway_tap.py`, `providers/payments/paytabs.py`) | VERIFIED |
| PayPal | `paypal` | Checkout SDK (`gateway_paypal.py`, `providers/payments/paypal.py`) | VERIFIED |
| Thawani Pay | `thawani` | HTTP REST API (`gateway_tap.py`, `providers/payments/thawani.py`) | VERIFIED |
| Custom/Generic | `custom` | Generic hosted-redirect adapter (`payment_orchestrator.py`) | VERIFIED |

**Evidence:**
- `backend/domains/finance/services/payments/payment_engine.py:313-317` — `BUILT_IN_GATEWAY_ORDER` and `BUILT_IN_GATEWAY_CODES`
- `backend/domains/finance/services/payments/payment_engine.py:299` — `SUPPORTED_CHECKOUT_PAYMENT_METHODS`
- `backend/providers/payments/stripe_sdk.py` — Stripe SDK wrapper
- `backend/providers/payments/tap.py` — Tap HTTP provider
- `backend/providers/payments/paytabs.py` — PayTabs HTTP provider
- `backend/providers/payments/paypal.py` — PayPal SDK wrapper
- `backend/providers/payments/thawani.py` — Thawani HTTP provider

### 1.2 Payment Flow Architecture (VERIFIED)

```
Frontend (checkout page)
    ↓
POST /orders → _calculate_order_amounts() [SERVER-SIDE]
    ↓ Order created with total_amount, payment_customer_total_amount
    ↓
POST /payments/{provider}/create → create_payment_intent / create_charge / create_checkout_session
    ↓ Gateway returns redirect URL / client secret
    ↓
Customer pays on gateway hosted page
    ↓
Gateway webhook → handle_{provider}_webhook / callback
    ↓ Signature verification → idempotency check → _apply_successful_payment()
    ↓ Order status: pending → confirmed, paid_at set, inventory finalized
    ↓
Frontend return URL → confirm endpoint (optional synchronous confirmation)
```

**Evidence:**
- `backend/domains/orders/services/core/order_engine.py:726` — `create_order()` calculates amounts server-side
- `backend/domains/finance/services/payments/payment_engine.py:3761` — `_order_charge_total_amount()` reads from order
- `backend/domains/finance/services/payments/gateway_stripe.py:47` — `create_payment_intent()`
- `backend/domains/finance/services/payments/payment_orchestrator.py:583` — `create_generic_gateway_payment()`

---

## 2. CRITICAL FINDINGS

### 2.1 [HIGH] Generic Gateway Callback — Missing Status Treated as Success

**Finding:** In `handle_generic_gateway_callback()`, when the callback payload does not contain an explicit status field, the system **automatically treats the callback as successful** and marks the order as paid.

**Status:** VERIFIED  
**Impact:** A malicious or misconfigured gateway could send an empty/no-status callback and the system would mark the order as paid without actual payment verification. This is a critical financial vulnerability.

**Files:**
- `backend/domains/finance/services/payments/payment_orchestrator.py:877-886`

**Symbols:**
- `handle_generic_gateway_callback()`
- `_GENERIC_DEFAULT_SUCCESS_VALUES`

**Code Evidence:**
```python
# Line 877-886
if not resolved_status:
    # No explicit status delivered (e.g. redirect-style return). Treat the
    # callback itself as an authorization to mark the order paid when the
    # gateway is configured without a status field.
    success = True
```

**Confidence:** High — Code explicitly shows unconditional `success = True` when status is empty.

---

### 2.2 [HIGH] Webhook Signature Verification — Optional/Skippable for Some Providers

**Finding:** Tap, PayTabs, and Thawani webhook signature verification is **conditionally skipped** when the webhook secret is not configured. The code logs a warning but continues processing the webhook.

**Status:** VERIFIED  
**Impact:** An attacker could send spoofed webhooks to these endpoints if the webhook secret is not configured (common in test/staging environments that may be promoted to production). This could lead to fraudulent order confirmations, refunds, or status changes.

**Files:**
- `backend/domains/finance/services/payments/gateway_tap.py:981-1003` — Tap webhook
- `backend/domains/finance/services/payments/gateway_tap.py:1415-1423` — Thawani webhook
- `backend/providers/payments/paytabs.py` — PayTabs provider (verification exists but is optional in callback)

**Symbols:**
- `handle_tap_webhook()`
- `handle_thawani_webhook()`
- `_verify_tap_signature()`

**Code Evidence (Tap):**
```python
# Line 981-1003
tap_webhook_secret = _resolve_tap_webhook_secret(db)
if tap_webhook_secret:
    sig_header = request.headers.get("hashstring", "")
    if not sig_header or not _verify_tap_signature(raw_body, sig_header, db):
        raise HTTPException(status_code=400, detail="Invalid Tap webhook signature")
else:
    # Secret not configured — log a warning but do NOT silently accept.
    logger.warning(
        "tap_webhook: TAP_WEBHOOK_SECRET is not configured; "
        "signature verification is skipped. Set TAP_WEBHOOK_SECRET in production."
    )
```

**Code Evidence (Thawani):**
```python
# Line 1415-1423
else:
    logger.warning(
        "thawani_webhook: THAWANI_WEBHOOK_SECRET is not configured; "
        "signature verification is skipped. Set thawani_webhook_secret in production."
    )
```

**Confidence:** High — Code clearly shows the fallback path where verification is skipped.

---

### 2.3 [MEDIUM] Stripe Refund — Stub Implementation When SDK Unavailable

**Finding:** `refund_payment_intent()` in `stripe_sdk.py` is a **stub** that returns a fake success response when the Stripe SDK is not installed.

**Status:** VERIFIED  
**Impact:** If the Stripe Python SDK is not installed in the environment, calling `refund_payment_intent()` returns `{"id": "stub_refund", "status": "succeeded"}` without actually processing a refund. This could lead to orders being marked as refunded without actual money being returned to the customer.

**Files:**
- `backend/providers/payments/stripe_sdk.py:27-34`

**Symbols:**
- `refund_payment_intent()`

**Code Evidence:**
```python
def refund_payment_intent(payment_intent_id: str, api_key: str = "") -> dict:
    """Stub for refunding a payment intent. Requires stripe SDK."""
    if HAS_STRIPE and stripe:
        try:
            return stripe.Refund.create(payment_intent=payment_intent_id)
        except Exception as exc:
            logger.warning("Failed to refund payment intent %s: %s", payment_intent_id, exc)
    return {"id": "stub_refund", "status": "succeeded"}
```

**Confidence:** High — Stub behavior is explicit in the code.

---

### 2.4 [MEDIUM] Amount Tampering Risk in Generic Gateway — No Server-Side Amount Verification

**Finding:** The generic gateway callback (`handle_generic_gateway_callback`) and confirmation (`confirm_generic_gateway_payment`) do **not re-verify the payment amount** against the order's stored amount. They trust the gateway's status response without checking if the paid amount matches `order.payment_customer_total_amount`.

**Status:** VERIFIED  
**Impact:** A compromised or misconfigured generic gateway could report a successful payment for a different amount than what the order requires. The system would mark the order as paid without verifying the amount.

**Files:**
- `backend/domains/finance/services/payments/payment_orchestrator.py:791-921` — `handle_generic_gateway_callback()`
- `backend/domains/finance/services/payments/payment_orchestrator.py:1033-1108` — `confirm_generic_gateway_payment()`

**Symbols:**
- `handle_generic_gateway_callback()`
- `confirm_generic_gateway_payment()`
- `_generic_verify_payment()`

**Code Evidence:**
```python
# Line 889-901 — No amount check before marking paid
if success and order.paid_at is None and order.status not in INVENTORY_RELEASE_STATUSES:
    if tran_ref:
        setattr(order, "payment_intent_id", tran_ref)
    _apply_successful_payment(order, f"Order #{order.id} payment via {normalized_code} was successful.", db)
```

**Contrast with Stripe (which DOES verify):**
```python
# payment_engine.py:4027-4047 — Stripe verifies amount in metadata
metadata_amount_minor = metadata.get("zozi_amount_minor")
intent_amount = _stripe_object_get(intent, "amount", None)
if metadata_amount_minor and intent_amount is not None:
    if int(str(intent_amount)) != int(metadata_amount_minor):
        return False, f"amount mismatch ({intent_amount} != {metadata_amount_minor})"
```

**Confidence:** High — Generic gateway code shows no amount verification.

---

### 2.5 [MEDIUM] Partial Refund Authorization — No Server-Side Amount Validation

**Finding:** Refund endpoints for Tap, PayPal, and PayTabs accept the refund amount from the request without validating it against the order's actual paid amount or remaining refundable balance.

**Status:** VERIFIED  
**Impact:** An attacker with access to the refund API could issue refunds for amounts greater than the original payment or for already-refunded orders. While the gateway itself may reject over-refunds, the ZOZI backend does not enforce this check.

**Files:**
- `backend/providers/payments/tap.py:201-260` — `refund_charge()`
- `backend/providers/payments/paypal.py:238-293` — `refund_payment()`
- `backend/providers/payments/paytabs.py:207-270` — `refund()`
- `backend/domains/orders/services/returns/service.py:429` — `_tap_refund_amount = Decimal(str(cast(Any, getattr(order, "total_amount")) or 0))` — uses order total without checking existing refunds

**Symbols:**
- `refund_charge()`
- `refund_payment()`
- `refund()`
- `update_return_request()` in returns service

**Code Evidence (Tap):**
```python
# tap.py:224-229
payload: dict[str, Any] = {
    "charge_id": charge_id,
    "reason": reason or "Refund",
}
if amount is not None:
    payload["amount"] = str(amount)
```

**Code Evidence (returns service — Tap auto-refund):**
```python
# returns/service.py:429
_tap_refund_amount = Decimal(str(cast(Any, getattr(order, "total_amount")) or 0))
```

**Confidence:** High — Refund functions accept arbitrary amounts without backend validation.

---

### 2.6 [MEDIUM] Race Condition — Double Order Confirmation / Double Inventory Deduction

**Finding:** While `ProcessedWebhookEvent` provides idempotency at the database level, there is a **potential race condition** if two webhooks for the same event arrive simultaneously. Both may pass the idempotency check before either commits, potentially leading to double inventory deduction or double order confirmation.

**Status:** INFERRED  
**Impact:** In high-traffic scenarios or with gateway retries, simultaneous webhook processing could result in double inventory deduction, double commission calculations, or duplicate notifications.

**Files:**
- `backend/domains/finance/services/payments/payment_engine.py:4143-4323` — `_finalize_inventory_for_paid_order()`
- `backend/domains/finance/services/payments/gateway_stripe.py:700-716` — Stripe webhook idempotency
- `backend/domains/finance/services/payments/gateway_tap.py:1031-1051` — Tap webhook idempotency

**Symbols:**
- `_finalize_inventory_for_paid_order()`
- `ProcessedWebhookEvent`
- `handle_stripe_webhook()`
- `handle_tap_webhook()`

**Code Evidence:**
```python
# gateway_stripe.py:700-716
if stripe_event_id:
    already_processed = db.query(ProcessedWebhookEvent).filter(
        ProcessedWebhookEvent.event_id == stripe_event_id,
        ProcessedWebhookEvent.processor == "stripe",
    ).first()
    if already_processed:
        return {"status": "ok"}
```

**Note:** The check-then-act pattern without a database-level unique constraint or `SELECT ... FOR UPDATE` creates a TOCTOU (Time-of-Check-Time-of-Use) race.

**Confidence:** Medium — Race condition is inferred from the check-then-act pattern without explicit locking.

---

### 2.7 [LOW] Checkout Page — Frontend Trusts Backend Totals (GOOD PRACTICE)

**Finding:** The frontend checkout page fetches totals from `/cart/totals` and `/admin/config/checkout` and uses those backend-calculated values for display. The actual order creation happens server-side in `_calculate_order_amounts()`.

**Status:** VERIFIED  
**Impact:** This is a **positive finding**. The frontend does NOT trust its own price calculations. All prices, discounts, taxes, and shipping are calculated server-side.

**Files:**
- `frontend/web_app/src/app/checkout/page.tsx:402-426` — Fetches `/cart/totals`
- `frontend/web_app/src/app/checkout/page.tsx:522-610` — Submits to `/orders` (not payment directly)
- `backend/domains/orders/services/core/order_engine.py:601-723` — `_calculate_order_amounts()` server-side

**Symbols:**
- `calculateSubtotal()` in checkoutHelpers.ts (frontend display only)
- `_calculate_order_amounts()` (backend authority)

**Confidence:** High — Code clearly shows backend is source of truth for pricing.

---

### 2.8 [LOW] Stripe SDK Key — Set Globally at Module Load

**Finding:** `stripe.api_key` is set at module level in `payment_engine.py:166` and updated dynamically via `_apply_stripe_runtime_key()`. The key is resolved from environment or database gateway connection records.

**Status:** VERIFIED  
**Impact:** Low risk. The key resolution supports per-request overrides from the database, which is good for multi-tenant/multi-country setups. However, the global mutation of `stripe.api_key` could cause issues in async contexts if not properly managed.

**Files:**
- `backend/domains/finance/services/payments/payment_engine.py:166-171`
- `backend/domains/finance/services/payments/payment_engine.py:1281-1293`

**Symbols:**
- `_apply_stripe_runtime_key()`
- `_resolve_stripe_secret_key()`

**Confidence:** High — Code shows the pattern.

---

## 3. CONFIRMED POSITIVE FINDINGS

### 3.1 Webhook Signature Verification — Implemented for All Major Providers

**Status:** VERIFIED

All major payment providers implement HMAC signature verification:
- **Stripe**: `stripe.Webhook.construct_event()` with `stripe-signature` header
- **Tap**: HMAC-SHA256 of raw body with `hashstring` header
- **PayTabs**: HMAC-SHA256 of raw body with `X-PAYTABS-SIGNATURE` header
- **PayPal**: PayPal's `/v1/notifications/verify-webhook-signature` API
- **Thawani**: HMAC-SHA256 of `{body}-{timestamp}` with `thawani-signature` header
- **Generic**: Configurable HMAC-SHA256 verification

**Files:**
- `backend/domains/finance/services/payments/gateway_stripe.py:652-688`
- `backend/domains/finance/services/payments/gateway_tap.py:925-965`
- `backend/providers/payments/paytabs.py:273-288`
- `backend/providers/payments/webhooks.py`
- `backend/domains/finance/services/payments/gateway_paypal.py:388-490`
- `backend/domains/finance/services/payments/payment_orchestrator.py:821-829`

### 3.2 Webhook Idempotency — Implemented via ProcessedWebhookEvent

**Status:** VERIFIED

All webhook handlers check `ProcessedWebhookEvent` before processing, preventing duplicate processing.

**Files:**
- `backend/domains/finance/services/payments/gateway_stripe.py:700-716`
- `backend/domains/finance/services/payments/gateway_tap.py:1031-1051`
- `backend/domains/finance/services/payments/gateway_tap.py:1167-1179`
- `backend/domains/finance/services/payments/gateway_paypal.py:410-422`
- `backend/domains/finance/services/payments/gateway_tap.py:1457-1469`

### 3.3 Order Amount Calculation — Server-Side Authority

**Status:** VERIFIED

All order amounts (subtotal, discount, tax, shipping, total) are calculated server-side in `_calculate_order_amounts()`. The frontend only sends item IDs and quantities.

**Files:**
- `backend/domains/orders/services/core/order_engine.py:601-723`

### 3.4 Payment Amount — Derived from Order, Not Frontend

**Status:** VERIFIED

Payment creation uses `_order_charge_total_amount(order)` which reads from the order's stored `payment_customer_total_amount` or `total_amount`. Frontend cannot manipulate the payment amount.

**Files:**
- `backend/domains/finance/services/payments/payment_engine.py:3761-3769`

### 3.5 IP Whitelist Middleware — Available for Webhooks

**Status:** VERIFIED

IP whitelist middleware exists for Stripe, Tap, PayPal, Thawani, PayTabs, and Resend webhooks.

**Files:**
- `backend/middleware/webhook_ip_whitelist.py`

### 3.6 Circuit Breaker Protection — All Gateways Protected

**Status:** VERIFIED

All payment gateway calls are protected by circuit breakers with failure thresholds and recovery timeouts.

**Files:**
- `backend/domains/finance/services/payments/payment_engine.py:178-186`

### 3.7 Payment Status Transitions — Guarded

**Status:** VERIFIED

Order status transitions are guarded:
- Already paid orders cannot be re-paid
- Closed orders (cancelled/refunded) cannot accept new payments
- Payment confirmation checks `order.paid_at is not None` and `order.status not in INVENTORY_RELEASE_STATUSES`

**Files:**
- `backend/domains/finance/services/payments/gateway_stripe.py:91-97`
- `backend/domains/finance/services/payments/payment_orchestrator.py:591-598`

---

## 4. PAYMENT FLOW TRACE — COMPLETE

### 4.1 Cart → Price Calculation → Checkout → Payment Creation

1. **Frontend** sends `POST /orders` with items, delivery details, payment method
2. **Backend** `create_order()` calls `_calculate_order_amounts()`:
   - Loads products from DB
   - Calculates subtotal from DB prices (NOT frontend prices)
   - Applies coupon discounts server-side
   - Applies tier discounts server-side
   - Calculates tax/VAT server-side
   - Calculates shipping server-side
   - Returns `total_amount`
3. **Order** is created with `total_amount`, `payment_customer_total_amount`, `payment_gateway_code`
4. **Frontend** receives order and initiates payment via `POST /payments/{provider}/create`
5. **Backend** creates payment intent/charge using `_order_charge_total_amount(order)` — reads from order, NOT frontend
6. **Gateway** returns redirect URL or client secret
7. **Frontend** redirects customer to gateway hosted page

### 4.2 Gateway → Callback/Webhook → Verification → Order State → Inventory → Notification

1. **Gateway** sends webhook/callback to backend
2. **Backend** verifies signature (HMAC or SDK-specific)
3. **Backend** checks `ProcessedWebhookEvent` for idempotency
4. **Backend** resolves order from transaction reference or order ID
5. **Backend** checks `order.paid_at is None` and `order.status not in INVENTORY_RELEASE_STATUSES`
6. **Backend** calls `_apply_successful_payment()`:
   - `_finalize_inventory_for_paid_order()` — deducts stock
   - Sets `order.paid_at`
   - Sets `order.status = "confirmed"`
   - Marks coupon as used
   - Increments sales counts
   - Creates ledger entries
   - Publishes `PaymentConfirmedEvent`
   - Sends notifications
7. **Frontend** return URL triggers confirmation endpoint (optional)

### 4.3 Failed Payments

- Stripe: `payment_intent.payment_failed` → order status set to `"failed"`
- Tap: Charge status `"FAILED"` → order status set to `"failed"`
- PayTabs: Response status in failure set → order status set to `"failed"`
- PayPal: Capture status `"VOIDED"` or `"DECLINED"` → order status set to `"failed"`

### 4.4 Refunds

- **Stripe**: `charge.refunded` webhook → `apply_order_status_change(order, "refunded")` → inventory restored → bank transaction logged
- **Tap**: Charge status `"REFUNDED"` webhook → same flow
- **PayPal**: `PAYMENT.CAPTURE.REFUNDED` webhook → same flow
- **Admin-initiated**: `refund_order()` → `refund_payment_intent()` → `apply_order_status_change()`
- **Return request**: `update_return_request()` with `status="completed"` and `intent="return"` → auto-refund via gateway

---

## 5. SECRETS AND API CREDENTIALS

### 5.1 Configuration Sources

Secrets are resolved from (in order of precedence):
1. Database `PaymentGatewayConnection` records (`secret_key`, `webhook_secret`, `public_key`, `merchant_id`)
2. Environment variables (`STRIPE_SECRET_KEY`, `TAP_SECRET_KEY`, `PAYTABS_SERVER_KEY`, etc.)
3. `settings` object (which reads from env)

**Evidence:**
- `backend/domains/finance/services/payments/payment_engine.py:1239-1259` — `_resolve_stripe_secret_key()`
- `backend/domains/finance/services/payments/payment_engine.py:1320-1331` — `_resolve_tap_secret_key()`
- `backend/providers/payments/config.py` — All provider config resolvers

### 5.2 Secret Exposure Risk

**Status:** VERIFIED — Secrets stored in database `PaymentGatewayConnection` table

The `secret_key`, `webhook_secret`, `public_key`, and `merchant_id` fields are stored in the `finance.payment_gateway_connections` table. While this is necessary for operation, these values should be encrypted at rest.

**Evidence:**
- `backend/domains/finance/models/payments.py:84-127` — `PaymentGatewayConnection` model
- `backend/domains/finance/services/payments/payment_engine.py:1834-1836` — PayPal credentials use `decrypt_secret()`
- `backend/domains/finance/services/payments/payment_engine.py:1916` — Thawani uses `decrypt_secret()`

**Note:** PayPal and Thawani credentials use `decrypt_secret()` indicating encryption. Stripe and Tap credentials appear to be stored in plain text in the database (resolved directly from `record.secret_key` without decryption).

---

## 6. CURRENCY AND AMOUNT HANDLING

### 6.1 Currency Resolution

Currency is determined server-side based on:
1. Request parameter
2. Country code
3. User profile preference
4. Default (`AED`)

**Evidence:**
- `backend/domains/finance/services/payments/payment_engine.py:3563-3568` — `_resolved_payment_currency()`

### 6.2 Amount Conversion

`convert_from_aed()` converts the base AED amount to the display currency. The amount sent to the gateway is the converted amount.

**Evidence:**
- `backend/domains/finance/services/payments/gateway_stripe.py:103` — `converted_total = convert_from_aed(charge_total, currency_code)`
- `backend/domains/finance/services/payments/gateway_tap.py:119` — `converted_total = convert_from_aed(charge_total, currency_code)`

### 6.3 Minor Units Handling

Stripe uses `money_to_minor_units_for_currency()` to convert to minor units (e.g., cents).

**Evidence:**
- `backend/domains/finance/services/payments/gateway_stripe.py:105` — `amount_minor = money_to_minor_units_for_currency(charge_total, currency_code)`

---

## 7. FRONTEND PAYMENT HANDLING

### 7.1 Checkout Flow

1. Frontend fetches `/cart/totals` for server-calculated totals
2. Frontend fetches `/payments/methods` for available payment methods
3. Frontend submits `POST /orders` with items and delivery details
4. Backend returns order with `total_amount`
5. Frontend initiates payment via provider-specific endpoint
6. Frontend redirects to gateway hosted page
7. Gateway redirects back to frontend with order ID in query params
8. Frontend calls confirmation endpoint (`/payments/confirm-card-payment`, `/payments/tap/confirm`, etc.)

**Evidence:**
- `frontend/web_app/src/app/checkout/page.tsx:522-610`

### 7.2 Frontend Does NOT Trust Own Prices

The frontend `calculateSubtotal()` in `checkoutHelpers.ts` is used only for display. The actual order creation and payment amounts are determined server-side.

**Evidence:**
- `frontend/web_app/src/shared/checkoutHelpers.ts:101-102` — `calculateSubtotal()` (display only)
- `frontend/web_app/src/app/checkout/page.tsx:409` — `apiFetch("/cart/totals")` (server authority)

---

## 8. UNKNOWN / NOT DETERMINABLE

1. **Database-level unique constraint on ProcessedWebhookEvent** — Not verified if a unique constraint exists on `(event_id, processor)` at the database level. The code checks for duplicates in Python but a DB constraint would provide stronger guarantees.

2. **Redis availability impact on idempotency** — `_check_payment_idempotency_key()` returns `None` if Redis is unavailable, effectively disabling idempotency for Stripe payment intent creation. The system continues without idempotency protection.

3. **Payment gateway fee calculation accuracy** — Gateway fees are calculated using hardcoded rates in `GATEWAY_FEE_RATES` (line 1333-1339 of `payment_orchestrator.py`) which may not match actual gateway fees.

4. **Double-check callback/confirm race** — The `confirm_generic_gateway_payment()` function has a check-then-act pattern that could race with a callback confirmation.

5. **PayPal webhook_id storage** — The PayPal webhook verification stores `webhook_id` in the `webhook_secret` field of `PaymentGatewayConnection`. This is a naming mismatch that could cause operational confusion.

---

## 9. SUMMARY TABLE

| # | Finding | Severity | Status | Provider(s) |
|---|---------|----------|--------|-------------|
| 2.1 | Generic gateway callback treats missing status as success | HIGH | VERIFIED | Custom/Generic |
| 2.2 | Webhook signature verification skippable for Tap/PayTabs/Thawani | HIGH | VERIFIED | Tap, PayTabs, Thawani |
| 2.3 | Stripe refund returns stub success when SDK unavailable | MEDIUM | VERIFIED | Stripe |
| 2.4 | Generic gateway does not verify payment amount | MEDIUM | VERIFIED | Custom/Generic |
| 2.5 | Partial refund amount not validated against order total | MEDIUM | VERIFIED | Tap, PayPal, PayTabs |
| 2.6 | Race condition in webhook idempotency (theoretical) | MEDIUM | INFERRED | All |
| 2.7 | Frontend trusts backend totals (GOOD) | LOW | VERIFIED | All |
| 2.8 | Global stripe.api_key mutation | LOW | VERIFIED | Stripe |

---

## 10. RECOMMENDATIONS (For Future Implementation — Not Part of Forensic Analysis)

1. **Generic Gateway**: Add explicit amount verification in `handle_generic_gateway_callback()` and `confirm_generic_gateway_payment()` by polling the gateway's verify endpoint and comparing the returned amount with `order.payment_customer_total_amount`.

2. **Webhook Secrets**: Enforce webhook secret configuration at startup for all providers. Do not allow processing webhooks without valid secrets in any environment that handles real transactions.

3. **Refund Validation**: Add server-side validation in all refund handlers to ensure the refund amount does not exceed the original payment amount minus previously refunded amounts.

4. **Database Constraints**: Add a unique constraint on `ProcessedWebhookEvent(event_id, processor)` at the database level to prevent race-condition duplicates.

5. **Stripe Refund Stub**: Remove the stub behavior from `refund_payment_intent()` and raise an explicit error when the Stripe SDK is unavailable.

6. **Webhook Verification**: Consider making `WebhookIPWhitelistMiddleware` mandatory (not optional) for all payment webhook paths.

7. **Redis Idempotency Fallback**: Add a database-level fallback for payment idempotency when Redis is unavailable.

---

*End of Phase 10 Payment Security Audit*
