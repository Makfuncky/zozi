"""Payments controller.

The payments domain — Stripe / Tap / PayPal / Thawani / PayTabs plus generic
hosted-redirect gateways, their webhooks, gateway connections, finance quotes
and the gateway setup wizard — is implemented in ``services.gateways.payments``.

This module is the controller boundary the router imports. It re-exports the
request models and handler functions so the router keeps a stable
``controllers.payments_controller`` namespace while the business logic stays in
the service layer.
"""
from __future__ import annotations

from services.gateways.payments import (
    ConfirmCardPaymentRequest,
)
from services.gateways.payments import (
    ConfirmGenericGatewayRequest,
)
from services.gateways.payments import (
    ConfirmPayTabsPaymentRequest,
)
from services.gateways.payments import (
    ConfirmTapPaymentRequest,
)
from services.gateways.payments import (
    ConfirmThawaniPaymentRequest,
)
from services.gateways.payments import (
    GatewayWizardRequest,
)
from services.gateways.payments import (
    GenericGatewayCreateRequest,
)
from services.gateways.payments import (
    PaymentFinanceQuoteRequest,
)
from services.gateways.payments import (
    PaymentGatewayConnectionRequest,
)
from services.gateways.payments import (
    PaymentIntentRequest,
)
from services.gateways.payments import (
    PaymentProviderRuntimeConfigRequest,
)
from services.gateways.payments import (
    PayPalCaptureRequest,
)
from services.gateways.payments import (
    PayPalOrderRequest,
)
from services.gateways.payments import (
    PayTabsChargeRequest,
)
from services.gateways.payments import (
    StripeCheckoutSessionRequest,
)
from services.gateways.payments import (
    TapChargeRequest,
)
from services.gateways.payments import (
    ThawaniCheckoutRequest,
)
from services.gateways.payments import (
    build_payment_finance_quote,
)
from services.gateways.payments import (
    capture_paypal_order,
)
from services.gateways.payments import (
    confirm_card_payment,
)
from services.gateways.payments import (
    confirm_generic_gateway_payment,
)
from services.gateways.payments import (
    confirm_paytabs_payment,
)
from services.gateways.payments import (
    confirm_tap_payment,
)
from services.gateways.payments import (
    confirm_thawani_payment,
)
from services.gateways.payments import (
    create_generic_gateway_payment,
)
from services.gateways.payments import (
    create_payment_intent,
)
from services.gateways.payments import (
    create_paypal_order,
)
from services.gateways.payments import (
    create_paytabs_charge,
)
from services.gateways.payments import (
    create_stripe_checkout_session,
)
from services.gateways.payments import (
    create_tap_charge,
)
from services.gateways.payments import (
    create_thawani_session,
)
from services.gateways.payments import (
    gateway_wizard_step,
)
from services.gateways.payments import (
    get_payment_methods_status,
)
from services.gateways.payments import (
    get_payment_provider_runtime_config,
)
from services.gateways.payments import (
    handle_generic_gateway_callback,
)
from services.gateways.payments import (
    handle_paypal_webhook,
)
from services.gateways.payments import (
    handle_paytabs_callback,
)
from services.gateways.payments import (
    handle_stripe_webhook,
)
from services.gateways.payments import (
    handle_tap_webhook,
)
from services.gateways.payments import (
    handle_thawani_webhook,
)
from services.gateways.payments import (
    list_payment_gateway_connections,
)
from services.gateways.payments import (
    test_payment_gateway_connection,
)
from services.gateways.payments import (
    update_payment_provider_runtime_config,
)
from services.gateways.payments import (
    upsert_payment_gateway_connection,
)

__all__ = [
    # Request models
    "ConfirmCardPaymentRequest",
    "ConfirmGenericGatewayRequest",
    "ConfirmPayTabsPaymentRequest",
    "ConfirmTapPaymentRequest",
    "ConfirmThawaniPaymentRequest",
    "GatewayWizardRequest",
    "GenericGatewayCreateRequest",
    "PaymentFinanceQuoteRequest",
    "PaymentGatewayConnectionRequest",
    "PaymentIntentRequest",
    "PaymentProviderRuntimeConfigRequest",
    "PayPalCaptureRequest",
    "PayPalOrderRequest",
    "PayTabsChargeRequest",
    "StripeCheckoutSessionRequest",
    "TapChargeRequest",
    "ThawaniCheckoutRequest",
    # Handlers
    "build_payment_finance_quote",
    "capture_paypal_order",
    "confirm_card_payment",
    "confirm_generic_gateway_payment",
    "confirm_paytabs_payment",
    "confirm_tap_payment",
    "confirm_thawani_payment",
    "create_generic_gateway_payment",
    "create_payment_intent",
    "create_paypal_order",
    "create_paytabs_charge",
    "create_stripe_checkout_session",
    "create_tap_charge",
    "create_thawani_session",
    "gateway_wizard_step",
    "get_payment_methods_status",
    "get_payment_provider_runtime_config",
    "handle_generic_gateway_callback",
    "handle_paypal_webhook",
    "handle_paytabs_callback",
    "handle_stripe_webhook",
    "handle_tap_webhook",
    "handle_thawani_webhook",
    "list_payment_gateway_connections",
    "test_payment_gateway_connection",
    "update_payment_provider_runtime_config",
    "upsert_payment_gateway_connection",
]
