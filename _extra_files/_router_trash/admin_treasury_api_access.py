"""Treasury API surface for ``routers.public_treasury_access``.

The treasury query/write functions were relocated into the service layer
(``services.treasury.treasury_query_service``) as part of the W1 circuit fix.
This module preserves the original ``routers.public_treasury_api_access`` import surface so
``routers.public_treasury_access`` keeps working without reaching into the service package
directly (avoids a router -> services circuit bypass).
"""
from __future__ import annotations

from data.services_treasury_treasury_query_service import (
    get_cash_position,
    get_supplier_payables,
    get_treasury_metrics,
    get_vat_liability,
)
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "get_cash_position",
    "get_supplier_payables",
    "get_treasury_metrics",
    "get_vat_liability",
]
