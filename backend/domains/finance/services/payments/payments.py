"""Payments service — backward-compatible shim.

This module is a thin re-export layer. All code has been moved to focused
sub-modules:
  - payment_engine: shared models, config, gateway CRUD, core processing
  - gateway_stripe: Stripe payment intent, checkout, webhook
  - gateway_paypal: PayPal orders, capture, webhook
  - gateway_tap: Tap, PayTabs, Thawani hosted-checkout flows and webhooks
  - payment_orchestrator: gateway wizard, generic gateway, reconciliation,
    auto-enable, badge billing
  - payment_event_handlers: re-exported webhook handlers

Import from the sub-modules directly for new code.
"""
from domains.finance.services.payments.payment_engine import *  # noqa: F401,F403
from domains.finance.services.payments.gateway_stripe import *  # noqa: F401,F403
from domains.finance.services.payments.gateway_paypal import *  # noqa: F401,F403
from domains.finance.services.payments.gateway_tap import *  # noqa: F401,F403
from domains.finance.services.payments.payment_orchestrator import *  # noqa: F401,F403
from domains.finance.services.payments.payment_event_handlers import *  # noqa: F401,F403

# Preserve explicit __all__ for backward compatibility
from domains.finance.services.payments.payment_engine import __all__ as _engine_all
from domains.finance.services.payments.gateway_stripe import __all__ as _stripe_all
from domains.finance.services.payments.gateway_paypal import __all__ as _paypal_all
from domains.finance.services.payments.gateway_tap import __all__ as _tap_all
from domains.finance.services.payments.payment_orchestrator import __all__ as _orch_all
from domains.finance.services.payments.payment_event_handlers import __all__ as _evt_all

__all__ = _engine_all + _stripe_all + _paypal_all + _tap_all + _orch_all + _evt_all
