"""Broker re-exporting order DTOs.

The historical ``order_dtos`` module was consolidated into ``dtos``; this thin
module preserves the original import path ``domains.orders.services.core.order_dtos``
so historical callers (e.g. order service / write facade) keep working
(Law 3 sanctioned re-export).
"""
from domains.orders.services.core.dtos import *  # noqa: F401,F403
from domains.orders.services.core.dtos import (  # noqa: F401
    OrderDTO,
    OrderItemDTO,
)
