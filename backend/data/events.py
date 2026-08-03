"""Event types for cross-ecosystem communication.

Re-exports PaymentConfirmedEvent from services.payments for use by services
that need to publish/subscribe to domain events without creating circular imports.
"""

from services.payments import PaymentConfirmedEvent

__all__ = ["PaymentConfirmedEvent"]