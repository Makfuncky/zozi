"""Payment gateway providers.

This package holds the complete payment-gateway connection logic. The controller
re-imports these symbols so existing call sites keep working during the migration.
"""
import structlog
logger = structlog.get_logger(__name__)

from providers.payments.config import *
from providers.payments.webhooks import *
from providers.payments.generic import *
from providers.payments.connect import *

__all__ = (
    list(config.__all__) + list(webhooks.__all__)
    + list(generic.__all__) + list(connect.__all__)
)
