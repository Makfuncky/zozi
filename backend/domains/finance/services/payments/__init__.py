"""Payments service package.

Sub-modules:
  - payment_engine: shared models, config, gateway CRUD, core processing
  - gateway_stripe: Stripe payment intent, checkout, webhook
  - gateway_paypal: PayPal orders, capture, webhook
  - gateway_tap: Tap, PayTabs, Thawani hosted-checkout flows and webhooks
  - payment_orchestrator: gateway wizard, generic gateway, reconciliation,
    auto-enable, badge billing
  - payment_event_handlers: re-exported webhook handlers
"""

# Explicit backward-compatible exports
from domains.finance.services.payments.payment_engine import (
    apply_order_status_change,
    build_order_payment_snapshot,
    confirm_cash_on_delivery_order,
    get_payment_methods_status,
    get_customer_checkout_gateways,
    get_payment_provider_runtime_config,
    list_payments,
    list_payment_gateway_connections,
    update_payment_provider_runtime_config,
    upsert_payment_gateway_connection,
    test_payment_gateway_connection,
    build_payment_finance_quote,
    normalize_checkout_payment_method,
    gateway_code_for_payment_method,
    is_checkout_payment_method_allowed,
    issue_stripe_refund,
)
from domains.finance.services.payments.gateway_stripe import (
    create_payment_intent,
    create_stripe_checkout_session,
    confirm_card_payment,
    handle_stripe_webhook,
)
from domains.finance.services.payments.gateway_paypal import (
    create_paypal_order,
    capture_paypal_order,
    handle_paypal_webhook,
)
from domains.finance.services.payments.gateway_tap import (
    create_tap_charge,
    confirm_tap_payment,
    create_paytabs_charge,
    confirm_paytabs_payment,
    handle_tap_webhook,
    handle_paytabs_callback,
    create_thawani_session,
    handle_thawani_webhook,
    confirm_thawani_payment,
)
from domains.finance.services.payments.payment_orchestrator import (
    gateway_wizard_step,
    create_generic_gateway_payment,
    confirm_generic_gateway_payment,
    handle_generic_gateway_callback,
    match_gateway_settlement,
    reconcile_cod_deposit,
    run_gateway_3way_reconciliation,
    reconcile_all_cod_deposits,
    GatewayAutoEnableService,
    auto_enable_gateways,
    list_badge_billing_records,
    get_badge_billing_record,
    generate_badge_billing_record,
    pay_badge_billing_record,
)
