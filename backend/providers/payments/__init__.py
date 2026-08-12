"""Payment gateway providers.

This package holds the complete payment-gateway connection logic. The controller
re-imports these symbols so existing call sites keep working during the migration.
"""
from providers.payments import _common, _order, config, webhooks, stripe, tap, paytabs, paypal, thawani, generic, connect
from providers.payments._common import *
from providers.payments._order import *
from providers.payments.config import *
from providers.payments.webhooks import *
from providers.payments.stripe import *
from providers.payments.tap import *
from providers.payments.paytabs import *
from providers.payments.paypal import *
from providers.payments.thawani import *
from providers.payments.generic import *
from providers.payments.connect import *
import structlog
logger = structlog.get_logger(__name__)

__all__ = (
    list(_common.__all__) + list(_order.__all__) + list(config.__all__)
    + list(webhooks.__all__) + list(stripe.__all__) + list(tap.__all__)
    + list(paytabs.__all__) + list(paypal.__all__) + list(thawani.__all__)
    + list(generic.__all__) + list(connect.__all__)
)
