"""Payment Gateway Adapters."""
from .base import BasePaymentGateway as PaymentGatewayAdapter
from .registry import PaymentGatewayRegistry
from .thawani import ThawaniAdapter
from .stripe import StripeAdapter
from .tap import TapAdapter

__all__ = [
    "PaymentGatewayAdapter",
    "PaymentGatewayRegistry",
    "ThawaniAdapter",
    "StripeAdapter",
    "TapAdapter",
]
