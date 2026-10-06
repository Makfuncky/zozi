"""customers domain — services sub-package."""
from __future__ import annotations

from domains.customers.services.customer_service import CustomerService
from domains.customers.services.core.customer_service import CustomerService as _CoreCustomerService  # noqa: F401
from domains.customers.services.customer_router_service import *
from domains.customers.services.customer_health_service import *
from domains.customers.services.customer_health_engine import *
from domains.customers.services.wishlist_service import *
from domains.customers.services.cart_service import *
from domains.customers.services.reviews_service import *
from domains.customers.services.search_service import *
from domains.customers.services.user_read_service import *
from domains.customers.services.coins import *
from domains.customers.services.recommendations import *

__all__: list[str] = ["CustomerService"]
