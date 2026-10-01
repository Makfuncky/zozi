"""suppliers domain - service layer package.

Owns all business logic and DB access for the suppliers domain. Module routers
import from here (never query the session directly). Services depend only on
infrastructure, kernel, providers (via services), and their own domain models
(per the dependency laws in ARCHITECTURE_DIAGRAM.md).
"""

from __future__ import annotations

from domains.suppliers.services.supplier_service import *
from domains.suppliers.services.supplier_shared import *
from domains.suppliers.services.profile.supplier_profile import *
from domains.suppliers.services.products.supplier_products import *
from domains.suppliers.services.orders.supplier_orders import *
from domains.suppliers.services.health.supplier_health import *

__all__ = []
