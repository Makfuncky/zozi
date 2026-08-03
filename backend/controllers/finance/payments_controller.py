"""Backward-compatible shim.

All payment logic has been moved to the service layer at
``services/finance/payments_gateway_service.py``.  This module re-binds the
``controllers.finance.payments_controller`` name to the service module so that
legacy imports (``from data.controllers_finance import payments_controller`` and
``from controllers.payments_controller import ...``) continue to resolve.
"""
import sys as _sys

from services.finance import payments_gateway_service as _svc

# Replace this module object in sys.modules so any caller that imports
# ``controllers.finance.payments_controller`` transparently gets the service
# module instead.  No controller logic remains here — W3 compliant.
_sys.modules[__name__] = _svc
