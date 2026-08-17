"""Controller seam for country-communications read endpoints.

Thin re-export so ``routers/country_communications.py`` can reach the
data-access helpers in
``services/geography/country_communication_service.py`` without importing
``services`` directly. All query/serialization logic lives in the service;
the router only handles WebSocket wiring and response shaping.
"""
from __future__ import annotations

from domains.country.services.country_communication_service import (
    get_cross_border_sessions,
    get_legal_contracts,
    get_partner_locations,
    get_shop_warehouses,
)

__all__ = [
    "get_cross_border_sessions",
    "get_legal_contracts",
    "get_shop_warehouses",
    "get_partner_locations",
]
