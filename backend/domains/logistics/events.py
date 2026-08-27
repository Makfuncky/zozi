"""Logistics domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Re-exports from services/events.py for public API consistency.
"""
from __future__ import annotations

from typing import Any

_LAZY_EXPORTS: dict[str, tuple[str, str]] = {
    # Event type constants
    "EVENT_SHIPMENT_CREATED": ("domains.logistics.services.events", "EVENT_SHIPMENT_CREATED"),
    "EVENT_SHIPMENT_IN_TRANSIT": ("domains.logistics.services.events", "EVENT_SHIPMENT_IN_TRANSIT"),
    "EVENT_SHIPMENT_DELIVERED": ("domains.logistics.services.events", "EVENT_SHIPMENT_DELIVERED"),
    # Event classes
    "LogisticsEvent": ("domains.logistics.services.events", "LogisticsEvent"),
    "ShipmentCreated": ("domains.logistics.services.events", "ShipmentCreated"),
    "ShipmentInTransit": ("domains.logistics.services.events", "ShipmentInTransit"),
    "ShipmentDelivered": ("domains.logistics.services.events", "ShipmentDelivered"),
    # Publish helpers
    "publish_shipment_created": ("domains.logistics.services.events", "publish_shipment_created"),
    "publish_shipment_in_transit": ("domains.logistics.services.events", "publish_shipment_in_transit"),
    "publish_shipment_delivered": ("domains.logistics.services.events", "publish_shipment_delivered"),
}


def __getattr__(name: str) -> Any:
    module_path, attr_name = _LAZY_EXPORTS.get(name, (None, None))
    if module_path is None:
        raise AttributeError(f"module 'domains.logistics.events' has no attribute {name!r}")
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, attr_name)


__all__ = list(_LAZY_EXPORTS.keys())
