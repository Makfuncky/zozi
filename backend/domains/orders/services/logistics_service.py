"""Orders-domain logistics controller.

Thin delegation layer used by the logistics module routers. Delegates to the
canonical logistics domain services while keeping the orders-domain import
surface stable.
"""
from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session


async def get_logistics_summary(current_user: dict, db: Session) -> dict:
    """Return logistics summary for the current user."""
    from domains.logistics.services.core.shipment_service import get_logistics_summary as _svc
    return await _svc(current_user, db)


async def get_carriers(current_user: dict, db: Session) -> list[dict]:
    """Return list of shipping carriers."""
    from domains.logistics.services.core.carrier_service import get_carriers as _svc
    return await _svc(current_user, db)


async def create_carrier(data: dict[str, Any], current_user: dict, db: Session) -> dict:
    """Create a new shipping carrier."""
    from domains.logistics.services.core.carrier_service import create_carrier as _svc
    return await _svc(data, current_user, db)


async def delete_carrier(carrier_id: int, current_user: dict, db: Session) -> dict:
    """Delete a shipping carrier."""
    from domains.logistics.services.core.carrier_service import delete_carrier as _svc
    return await _svc(carrier_id, current_user, db)


async def get_shipping_zones(current_user: dict, db: Session) -> list[dict]:
    """Return list of shipping zones."""
    from domains.logistics.services.core.zone_service import get_shipping_zones as _svc
    return await _svc(current_user, db)


async def upsert_shipping_zone(data: dict[str, Any], current_user: dict, db: Session) -> dict:
    """Create or update a shipping zone."""
    from domains.logistics.services.core.zone_service import upsert_shipping_zone as _svc
    return await _svc(data, current_user, db)


async def delete_shipping_zone(zone_id: int, current_user: dict, db: Session) -> dict:
    """Delete a shipping zone."""
    from domains.logistics.services.core.zone_service import delete_shipping_zone as _svc
    return await _svc(zone_id, current_user, db)


async def get_orders_to_fulfil(
    current_user: dict,
    db: Session,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    """Return orders awaiting fulfilment."""
    from domains.logistics.services.core.shipment_service import get_orders_to_fulfil as _svc
    return await _svc(current_user, db, limit=limit, offset=offset)


async def create_shipment(data: dict[str, Any], current_user: dict, db: Session) -> dict:
    """Create a new shipment."""
    from domains.logistics.services.core.shipment_service import create_shipment as _svc
    return await _svc(data, current_user, db)


async def get_active_shipments(current_user: dict, db: Session) -> list[dict]:
    """Return active shipments."""
    from domains.logistics.services.core.shipment_service import get_active_shipments as _svc
    return await _svc(current_user, db)


async def get_shipment_history(
    current_user: dict,
    db: Session,
    page: int = 1,
    per_page: int = 30,
) -> dict:
    """Return paginated shipment history."""
    from domains.logistics.services.core.shipment_service import get_shipment_history as _svc
    return await _svc(current_user, db, page=page, per_page=per_page)


async def get_shipment_events(shipment_id: int, current_user: dict, db: Session) -> list[dict]:
    """Return events for a shipment."""
    from domains.logistics.services.core.shipment_service import get_shipment_events as _svc
    return await _svc(shipment_id, current_user, db)


async def scan_shipment_event(
    shipment_id: int,
    data: dict[str, Any],
    current_user: dict,
    db: Session,
) -> dict:
    """Record a scan event for a shipment."""
    from domains.logistics.services.core.shipment_service import scan_shipment_event as _svc
    return await _svc(shipment_id, data, current_user, db)


async def update_shipment_status(
    shipment_id: int,
    data: dict[str, Any],
    current_user: dict,
    db: Session,
) -> dict:
    """Update shipment status."""
    from domains.logistics.services.core.shipment_service import update_shipment_status as _svc
    return await _svc(shipment_id, data, current_user, db)


async def get_distribution_channels(current_user: dict, db: Session) -> list[dict]:
    """Return available distribution channels."""
    from domains.logistics.services.core.shipment_service import get_distribution_channels as _svc
    return await _svc(current_user, db)


async def update_event_gps(
    event_id: int,
    lat: float,
    lng: float,
    current_user: dict,
    db: Session,
) -> dict:
    """Attach GPS coordinates to a shipment event."""
    from domains.logistics.services.core.shipment_service import update_event_gps as _svc
    return await _svc(event_id, lat, lng, current_user, db)
