```
=== AGENT LOG ===
PHASE: 10 — Payment System Forensic & Security Audit
STATUS: COMPLETED
REPORT_FILE: _audit/findings/PHASE_10_PAYMENT_SECURITY.md
SCOPE_COVERED: Payment providers (Stripe, Tap, PayTabs, Thawani, PayPal, generic hosted-redirect, COD); intent/session/charge creation; callbacks/webhooks; signature verification; idempotency; order↔payment binding; amount/currency calculation; discounts/tax/shipping; refunds; inventory finalization; secret handling; frontend payment handling; webhook middleware (HMAC + IP whitelist).
FILES_EXAMINED: ~22
EVIDENCE_ITEMS: ~60 file:line citations
FINDINGS_TOTAL: 15  (VERIFIED: 12 / INFERRED: 3 / UNKNOWN: 0)
SEVERITY_BREAKDOWN: BLOCKER: 1 / HIGH: 4 / MEDIUM: 6 / LOW: 4 / INFO: 0
TOP_FINDINGS:
  1. Generic gateway callback fail-open + "no status = paid" + trusts body order_id — payment bypass — backend/domains/finance/services/payments/payment_orchestrator.py:791-905
  2. Tap/PayTabs confirm+finalize never verify charge amount or order binding — underpayment — backend/domains/finance/services/payments/gateway_tap.py:283-330, 492-533, 628-665, 887-905
  3. Fail-open webhook signatures (Tap/Thawani/Generic/PayPal-on-error) when secret unset — backend/domains/finance/services/payments/gateway_tap.py:971-1000, 1367-1417
  4. HMAC + IP-whitelist middleware only guards Stripe/Tap/Resend; Thawani/PayPal/PayTabs/Generic bypass it — backend/middleware/webhook_verification.py:67-71 ; backend/middleware/webhook_ip_whitelist.py:391-395
  5. Payment finalization has no row lock → double inventory/ledger under concurrency — backend/domains/finance/services/payments/payment_engine.py:4435-4520
GAPS / NOT DETERMINABLE: Runtime value of `field_encryptor` (is at-rest encryption enabled?) not determinable from code alone; exact live-vs-test config of each gateway's webhook_secret is deployment-time; whether the misplaced `.limit(1000)` (F15) is the deployed source or an artifact requires a runtime check.
SELF_SKEPTICISM_RATING: 4
=== END AGENT LOG ===
```

# PHASE 10 — Payment System Forensic & Security Audit

> Scope: **payment functionality only**. Forensic, evidence-based, skeptical.
> READ-ONLY on codebase. No secret values reproduced. Findings are split into
> **CONFIRMED** (directly evidenced in code) and **POTENTIAL** (requires runtime
> or deployment verification). Labels: **VERIFIED / INFERRED / UNKNOWN**.

---

## 0. Payment providers actually present (VERIFIED)

Traced from concrete adapters + routes, not names/docs:

| Provider | Kind | Create | Confirm (sync) | Webhook/Callback | Evidence |
|---|---|---|---|---|---|
| **Stripe** | card intent + hosted session | `create_payment_intent`, `create_stripe_checkout_session` | `confirm_card_payment` | `handle_stripe_webhook` | [gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L47) |
| **Tap** | hosted charge | `create_tap_charge` | `confirm_tap_payment` | `handle_tap_webhook` | [gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L492) |
| **PayTabs** | hosted redirect | `create_paytabs_charge` | `confirm_paytabs_payment` | `handle_paytabs_callback` | [gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L887) |
| **Thawani** | hosted session (OMR) | `create_thawani_session` | `confirm_thawani_payment` | `handle_thawani_webhook` | [gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L1367) |
| **PayPal** | order + capture | `create_paypal_order` | `capture_paypal_order` | `handle_paypal_webhook` | [gateway_paypal.py](../../backend/domains/finance/services/payments/gateway_paypal.py#L207) |
| **Generic / custom** | any hosted-redirect gateway | `create_generic_gateway_payment` | `confirm_generic_gateway_payment` | `handle_generic_gateway_callback` | [payment_orchestrator.py](../../backend/domains/finance/services/payments/payment_orchestrator.py#L544) |
| **Cash on Delivery** | offline | order confirmed at creation | n/a | n/a | [payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4600) |

Routes are exposed under the customer finance router: [modules/customer/routers/finance.py](../../backend/modules/customer/routers/finance.py#L189-L342).
Canonical implementation lives in `domains/finance/services/payments/*`; the
`domains/payments/services/payment_service.py` layer is a thin wrapper that
delegates to `domains.finance.ports` (VERIFIED: [payment_service.py](../../backend/domains/payments/services/payment_service.py#L26)).

---

## 1. Full flow trace (what the code actually does)

**Cart → price → checkout → order:**
`create_order` → `_calculate_order_amounts` computes **server-side**:
`subtotal = Σ(Product.price × qty)`, coupon discount via `build_coupon_quote`,
tier discount, tax, shipping, then `total_amount`
([order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L646-L706)).
Stock is **validated** (with `with_for_update()`) but **not decremented** at creation
([order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L216-L245)).

**Order → payment creation:** payment endpoints load the order via
`_get_user_order` (ownership enforced), recompute the charge from
`_order_charge_total_amount(order)` = `order.payment_customer_total_amount || order.total_amount`
([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L3761)),
convert with `convert_from_aed`, and build the PSP request. **Amount is derived
from the persisted order, never from the client** (VERIFIED — Stripe:
[gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L88-L100); Tap:
[gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L115-L119)).

**Gateway → callback/webhook → verification → order state → inventory → notification:**
success paths call `_apply_successful_payment` → `_confirm_order(mark_paid=True)` →
`_finalize_inventory_for_paid_order` (deduct stock) + coupon use + sales counts +
GL ledger + notification
([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4435-L4520)).

---

## 2. Trust model (does the system trust the client?)

| Input | Trusted? | Evidence |
|---|---|---|
| Frontend **prices** | **NO** — recomputed from `Product.price` | [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L660-L706) — VERIFIED |
| Frontend **quantities** | Partially — used as requested but stock-validated; priced server-side | [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L216-L245) |
| Frontend **discounts/coupons** | **NO** — coupon looked up & quoted server-side | [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L671-L676) — VERIFIED |
| Frontend **payment status** | **NO** for Stripe (verified intent), Tap/PayTabs/Thawani (server re-query), PayPal (server capture); **YES (partial)** for generic callback | See F1, §3 |
| **Webhook data without signature** | **YES when secret unset** (fail-open) for Tap/Thawani/Generic; PayPal continues on verify error | See F1, F3 |

**Bottom line:** classic *frontend price/discount tampering is NOT viable* — the
order total is authoritative and server-computed. The exploitable surface is the
**gateway callback/confirmation trust boundary**, not cart pricing.

---

## 3. CONFIRMED FINDINGS

### F1 — Generic gateway callback: fail-open signature + "no status ⇒ paid" + trusts body `order_id`  (CONFIRMED — BLOCKER/CRITICAL, VERIFIED)
**Evidence:** `handle_generic_gateway_callback`
[payment_orchestrator.py](../../backend/domains/finance/services/payments/payment_orchestrator.py#L791-L905):
- Signature is only checked *if a webhook secret exists*: `if webhook_secret: … _verify_paytabs_signature(...)` — **when no secret is configured the check is skipped entirely** (lines ~836-843).
- Order is resolved from attacker-controlled body: `_resolve_generic_order` reads `order_id`/`cart_id` straight from the payload ([payment_orchestrator.py](../../backend/domains/finance/services/payments/payment_orchestrator.py#L648-L676)); order IDs are sequential integers.
- **Default-to-success:** `if not resolved_status: success = True` — a callback with *no status field* is treated as a successful payment (lines ~878-882), then `_apply_successful_payment` marks the order paid.
- **No amount check** against `order.total_amount`.
- The route `/payments/generic/{provider_code}/callback` is provider-facing/unauthenticated and is **not** covered by the HMAC or IP-whitelist middleware (see F4).

**Impact:** An unauthenticated attacker who knows/guesses an order id can POST an empty/benign body to the generic callback for any gateway that has no webhook secret configured and mark that order **paid** (payment bypass), triggering fulfillment + inventory deduction.
**Remediation:** Require a configured webhook secret (fail-closed); never treat "missing status" as success; verify the gateway-reported amount == `order.total_amount`; bind the callback to a server-issued opaque reference (`payment_intent_id`) rather than the client-supplied order id; register the path in the webhook HMAC/IP middleware.

---

### F2 — Tap / PayTabs confirm & finalize never verify charge **amount** or **order binding**  (CONFIRMED — HIGH, VERIFIED)
**Evidence:**
- `confirm_tap_payment` uses the **client-supplied** charge id first: `charge_id = (body.charge_id or order.payment_intent_id …)` ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L503)), fetches that charge server-side, then calls `_finalize_tap_charge_status`.
- `_finalize_tap_charge_status` acts **only** on `status == "CAPTURED"` and does **not** compare `charge_payload["amount"]` to the order total, nor `charge_payload["reference"]["order"] / metadata["order_id"]` to `order.id` ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L283-L330)) — even though the Tap charge is *created* with both `reference.order` and `metadata.order_id` ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L124-L138)).
- Same pattern for PayTabs: `confirm_paytabs_payment` takes `body.tran_ref` ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L887-L905)); `_finalize_paytabs_transaction` marks paid on success status only, no amount/binding check ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L628-L665)); `handle_paytabs_callback` resolves the order by body `cart_id`, re-queries PayTabs by the body `tran_ref`, and finalizes with no amount check ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L1083-L1140)).

**Impact:** An authenticated buyer can create a large order A and a cheap order B, pay B (small `charge_id`/`tran_ref`), then call `POST /payments/tap/confirm` (or `/paytabs/confirm`) with `order_id = A` and the *cheap* charge/tran ref → order A is marked fully paid for a fraction of its value (**underpayment / amount substitution**). The data needed to prevent this (amount, embedded order id) is present in the gateway response but ignored.
**Remediation:** In every finalize path, assert `gateway_amount == order.total_amount` (in the charge currency) **and** the charge's embedded order/customer reference == this order/user before applying payment; ignore client-supplied charge ids that don't match the order's stored intent.

---

### F3 — Fail-open webhook signature verification when secret unset  (CONFIRMED — HIGH, VERIFIED)
**Evidence:**
- Tap: `if tap_webhook_secret: … verify … else: logger.warning(…skipped…)` and **processes anyway** ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L971-L1000)).
- Thawani: identical fail-open branch ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L1367-L1417)).
- Generic: fail-open (F1).
- PayPal: signature verified only when `client_id && secret && webhook_id` are all set, and the verification is wrapped so that `except Exception: logger.exception(...)` **swallows verify-call failures and continues** processing (only the explicit "invalid" `HTTPException` re-raises) ([gateway_paypal.py](../../backend/domains/finance/services/payments/gateway_paypal.py#L424-L470)).
- Contrast — Stripe **fails closed**: `if not webhook_secret: raise 503` ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L653-L656)).

**Impact:** If a gateway's webhook secret is not configured (a plausible/likely default state, since gateways are admin-provisioned at runtime), the corresponding webhook accepts spoofed payloads and can mark orders paid/failed/refunded.
**Remediation:** Fail closed for all providers (reject when secret missing); for PayPal, only continue when verification returns `SUCCESS` — treat verify-call errors as rejection, not acceptance.

---

### F4 — Webhook HMAC + IP-whitelist middleware only guards Stripe/Tap/Resend; other providers bypass it; Tap scheme mismatch  (CONFIRMED — HIGH, VERIFIED / contradiction)
**Evidence:**
- HMAC middleware `WEBHOOK_PATHS = {"/payments/webhook", "/payments/tap/webhook", "/email/webhooks"}` ([webhook_verification.py](../../backend/middleware/webhook_verification.py#L67-L71)); IP whitelist `WEBHOOK_PATH_PREFIXES` is the same set ([webhook_ip_whitelist.py](../../backend/middleware/webhook_ip_whitelist.py#L391-L395)). Both middlewares are registered ([orchestrator.py](../../backend/middleware/orchestrator.py#L108-L111)).
- Routes exist for `/paytabs/callback`, `/paypal/webhook`, `/thawani/webhook`, `/generic/{code}/callback` ([finance.py](../../backend/modules/customer/routers/finance.py#L316-L342)) — **none** are in the middleware sets ⇒ they bypass HMAC + IP whitelisting and rely solely on the fail-open service checks (F1/F3).
- **Scheme contradiction:** the middleware expects a `Tap-Signature: t=…,v1=…` timestamped HMAC ([webhook_verification.py](../../backend/middleware/webhook_verification.py#L45-L50), `_compute_signature` L184-L196), but the Tap service verifies a `hashstring` header = `HMAC(secret, raw_body)` with no timestamp ([gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L919-L965)). The two are mutually incompatible; a genuine Tap webhook (`hashstring`, no `Tap-Signature`) would be rejected 401 by the middleware, so either Tap webhooks are broken or the middleware secret is empty and both layers no-op.

**Impact:** Defense-in-depth (crypto verification + source-IP restriction) is absent for 4 of 6 online providers; the Tap scheme mismatch is an internal contradiction that undermines the one non-Stripe provider the middleware claims to cover.
**Remediation:** Extend `WEBHOOK_PATHS`/`WEBHOOK_PATH_PREFIXES` to every provider callback; reconcile the Tap signature scheme between middleware and service (pick one); add integration tests asserting a valid provider payload passes end-to-end.

---

### F5 — Payment finalization race: no row lock ⇒ double inventory deduction / double ledger  (CONFIRMED — HIGH, VERIFIED code / INFERRED exploitability)
**Evidence:** Every success path guards only with an unlocked read `order.paid_at is None` (Stripe [gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L786-L806); Tap [gateway_tap.py](../../backend/domains/finance/services/payments/gateway_tap.py#L293-L305); generic [payment_orchestrator.py](../../backend/domains/finance/services/payments/payment_orchestrator.py#L883-L896)). The order row is **not** selected `with_for_update`, and `_finalize_inventory_for_paid_order` decrements `Product.stock` with no idempotency marker ([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4143-L4260)). `ProcessedWebhookEvent` dedups *identical* webhook events only; a webhook racing the synchronous `confirm_*` endpoint (different keys) is not covered.
**Impact:** Concurrent confirm+webhook (or two distinct provider events) can both pass the guard → stock deducted twice, `sales_count` incremented twice, duplicate GL/bank-ledger entries, and a second gateway-side action.
**Remediation:** Lock the order row (`SELECT … FOR UPDATE`) around the check-then-act, or add a DB-level idempotency/uniqueness guard on "payment applied for order".

---

### F6 — Return→refund path: full refund only, no idempotency, ignores `refund_amount`  (CONFIRMED — MEDIUM, VERIFIED)
**Evidence:** `update_return_request` (admin/support gated — [returns/service.py](../../backend/domains/orders/services/returns/service.py#L367-L368)) issues a **full** refund on completion: Stripe `refund_payment_intent(payment_id)` with no amount, Tap `refund_tap_charge(payment_id, order.total_amount, …)` ([returns/service.py](../../backend/domains/orders/services/returns/service.py#L389-L465)). There is **no check that the order/return was already refunded/completed** before calling the gateway refund, and `ReturnRequest.refund_amount` (partial) is never applied.
**Impact:** (a) Re-completing a return, or two return requests for the same order, triggers **duplicate gateway refunds** (financial loss); (b) partial-return requests refund the entire order (over-refund).
**Remediation:** Guard on `order.status == "refunded"` / return already completed before refunding; make the gateway refund idempotent (idempotency key / dedupe); honor `refund_amount` for partial refunds.

---

### F7 — Minor-unit bug for 3-decimal currencies + static FX rates  (CONFIRMED — MEDIUM, VERIFIED)
**Evidence:** `money_to_minor_units_for_currency` always multiplies by 100 ("treat everything as 2dp for safety") ([money_utils.py](../../backend/domains/finance/services/payments/money_utils.py#L33-L40)); this value feeds Stripe `amount` and other minor-unit charges ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L90-L96)). OMR/KWD/BHD are **3-decimal** (×1000) currencies, so a charge in those currencies via the minor-units path is understated by 10×. `convert_from_aed` uses hardcoded static rates and a **1:1 fallback for unknown currencies** ([money_utils.py](../../backend/domains/finance/services/payments/money_utils.py#L15-L31)).
**Impact:** Under/over-charging for 3-decimal currencies; stale/■incorrect FX for all currencies; unknown currency charged as if AED.
**Remediation:** Use a per-currency minor-unit exponent table (2 vs 3 dp); source FX from a live/authoritative provider; reject unknown currencies instead of 1:1.

---

### F8 — Gateway secrets not encrypted at rest; inconsistent read path  (CONFIRMED — MEDIUM, VERIFIED code / INFERRED at-rest state)
**Evidence:** Stripe/Tap secret & webhook secret are read as **plaintext** `getattr(record, "secret_key")` ([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L1265-L1360)), whereas PayPal/Thawani read via `decrypt_secret` ([gateway_paypal.py](../../backend/domains/finance/services/payments/gateway_paypal.py#L434)). The `decrypt_secret` used there is a **passthrough** when `field_encryptor` is unavailable ([utils/encryption.py](../../backend/infrastructure/utils/encryption.py#L31-L52)), and no `encrypt_secret` call exists on the gateway write path (grep across `backend/**`). Secrets live in `finance.payment_gateway_connections` (`secret_key`, `webhook_secret`, `public_key`).
**Impact:** Payment API keys and webhook secrets are likely stored in the DB without at-rest encryption; a DB read (backup, injection, over-broad access) discloses live gateway credentials. The read inconsistency also risks decrypt/mismatch bugs if encryption is later enabled.
**Remediation:** Encrypt gateway secrets on write (single helper) and decrypt on read consistently; verify `field_encryptor` is configured in production; restrict/segregate the connections table. *(No secret values are reproduced in this report.)*

---

### F9 — `charge.refunded` restores full inventory / sets `refunded` regardless of partial amount  (CONFIRMED — MEDIUM, VERIFIED)
**Evidence:** Stripe `charge.refunded` handler calls `apply_order_status_change(order, "refunded", db)` and restores inventory on any refund event, without inspecting the refunded amount vs order total ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L855-L905)); `apply_order_status_change` restocks the whole order ([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4389-L4410)).
**Impact:** A partial refund flips the order to fully `refunded` and restocks all items → inventory/accounting drift.
**Remediation:** Distinguish partial vs full refunds; only transition to `refunded` and restock when the cumulative refunded amount equals the captured total.

---

### F10 — Payment/inventory finalization contains a misplaced `.limit(1000)` (runtime crash risk)  (CONFIRMED in source — BLOCKER, VERIFIED source / INFERRED runtime)
**Evidence:** In `_finalize_inventory_for_paid_order` the products dict-comprehension value is `p .limit(1000)` (i.e. `p.limit(1000)` on a `Product` instance), and the same misplacement appears in `_restore_inventory_for_order` ([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4165-L4168) and [payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L4338-L4344)).
**Impact:** If this is the deployed source, `Product.limit` does not exist ⇒ `AttributeError` when finalizing a paid order, causing `_apply_successful_payment` to raise and **every card/online payment finalization + every inventory restore to fail** (500s; orders paid at the gateway but never confirmed). This looks like a botched automated edit.
**Confidence/UNKNOWN:** Whether this exact text is what runs in the target environment must be confirmed at runtime (the doubled-blank-line formatting throughout these files suggests machine rewriting).
**Remediation:** Move `.limit(1000)` onto the `db.query(...)` call (as done correctly in `_load_products_for_order` [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L233-L240)); add a smoke test that finalizes a paid order.

---

## 4. POTENTIAL FINDINGS (require runtime/deployment verification)

### F11 — Webhook IP allow-list is bypassable via `X-Forwarded-For`  (POTENTIAL — MEDIUM, VERIFIED code)
`_extract_client_ip` trusts the first `X-Forwarded-For` value ([webhook_ip_whitelist.py](../../backend/middleware/webhook_ip_whitelist.py#L398-L409)). Unless an upstream proxy strips/overwrites XFF, an attacker can spoof a whitelisted provider IP. **Remediation:** derive client IP only from the trusted proxy hop; ignore inbound XFF.

### F12 — Sequential order IDs used as gateway `cart_id` / `client_reference_id`  (POTENTIAL — MEDIUM, VERIFIED)
`Order.id` is an auto-increment integer ([order_entities.py](../../backend/domains/orders/models/order_entities.py#L20-L58)) and is used directly as PayTabs `cart_id` and Thawani `client_reference_id`, and is trusted by the generic callback. Guessable ids amplify F1/F2 on unauthenticated callbacks. **Remediation:** use an opaque per-payment reference for provider binding.

### F13 — `require_feature("finance.ledger.write")` on webhook routes is ambiguous  (POTENTIAL — LOW, INFERRED)
Webhook routes depend on `require_feature("finance.ledger.write")` ([finance.py](../../backend/modules/customer/routers/finance.py#L301-L342)), which resolves features from an *optional* user ([rbac/dependencies.py](../../backend/rbac/dependencies.py#L106-L131)). For unauthenticated providers this either 403s legitimate webhooks or is a no-op for anonymous callers. **Remediation:** gate webhooks by signature/IP, not by a user feature flag.

### F14 — Server-side tax path is dead; always falls back to flat VAT  (POTENTIAL — LOW, VERIFIED)
`calculate_tax`/`get_country_config` imports are commented out ("Module not yet created") ([order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L54-L58)) yet `calculate_tax(...)` is called ([order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L688)); the `NameError` is caught and the code always falls back to `settings.vat_rate` ([order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L693-L699)). Affects charged amount correctness (not a bypass). Same dead-import pattern for `FraudScoringEngine` (fraud scoring silently disabled — [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L739-L770)).

### F15 — CSRF/webhook exemption lists omit non-Stripe/Tap callbacks  (POTENTIAL — LOW, VERIFIED)
CSRF exempt paths list only `/payments/webhook`, `/payments/tap/webhook`, `/email/webhooks` ([csrf_middleware.py](../../backend/middleware/csrf_middleware.py#L22-L24)); Thawani/PayPal/PayTabs/generic callbacks are absent. Likely benign (webhooks are cookieless POSTs) but inconsistent; verify no CSRF/other middleware blocks these provider POSTs.

---

## 5. Controls that ARE correctly implemented (VERIFIED — for balance)

- **Order totals are fully server-computed**; frontend prices/discounts are not trusted (F-trust table; [order_engine.py](../../backend/domains/orders/services/core/order_engine.py#L646-L706)).
- **Stripe** webhook uses `stripe.Webhook.construct_event` (real signature), fails closed on missing secret, dedups via `ProcessedWebhookEvent`, and validates intent↔order via metadata `order_id`/`user_id`/`zozi_amount_minor`/`display_currency` ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L652-L700); `_payment_intent_matches_order` [payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L3991-L4030)).
- **Stripe intent/session amounts** are computed from the order and pinned in metadata (`zozi_amount_minor`), and the intent is re-validated on reuse ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L88-L140)).
- **Confirm endpoints** require authentication and enforce order ownership via `_get_user_order`.
- **Refund approval** requires `admin`/`support` role ([returns/service.py](../../backend/domains/orders/services/returns/service.py#L367-L368)).
- **Redis idempotency** for intent creation via `idempotency_key` ([payment_engine.py](../../backend/domains/finance/services/payments/payment_engine.py#L60-L110)) and Stripe SDK `idempotency_key` on create ([gateway_stripe.py](../../backend/domains/finance/services/payments/gateway_stripe.py#L150-L170)).
- **Money stored as `Numeric`** (no float) in payment models ([payment_models.py](../../backend/domains/payments/models/payment_models.py#L110-L200)).
- **No hardcoded live secrets** in application code (only `sk_test_/sk_live_` *prefix patterns* and test fixtures; grep across `backend/**`).
- **No logging of secret values** detected (grep for `logger.*secret_key|webhook_secret|api_key` → none).

---

## 6. Skepticism / limitations

- Line numbers reference the ranges actually read; these files contain machine-inserted doubled blank lines, so exact line offsets may drift by a few lines — function names + cited ranges are authoritative.
- At-rest encryption state (F8) and per-gateway webhook-secret configuration (F1/F3) are **deployment/runtime** facts not fully determinable from source.
- F10 is present in source but its runtime effect is INFERRED; confirm with a live "confirm a paid order" smoke test before treating as an active outage vs. an audit-only defect.
- Framework/DB-level constraints (e.g., `chk_payment_intent_status_valid`) exist but do **not** substitute for the missing application-level amount/binding checks in F1/F2.
```
