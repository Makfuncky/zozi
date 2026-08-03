"""Controllers package - domain-organized modules.

Controllers are organized by domain subdomain (catalog, finance, orders, etc.).
Re-export stubs in the root directory provide backward compatibility.
"""

# Subdirectory controllers that import cleanly
from .country import country_controller
from .finance import accounting_controller, commission_controller, payments_controller
from .orders import cart_controller, disputes_controller, returns_controller
from .security import auth_controller, iam_controller, risk_controller
from .supplier import supplier_controller
from .communication import email_controller

__all__ = [
    'country_controller', 'accounting_controller', 'commission_controller', 'payments_controller',
    'cart_controller', 'disputes_controller', 'returns_controller',
    'auth_controller', 'iam_controller', 'risk_controller',
    'supplier_controller', 'email_controller',
]