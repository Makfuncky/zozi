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