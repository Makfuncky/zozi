"""logistics domain controller (AXIS 2).

Adapts the logistics-module User ORM object into the dict shape expected by the
orders-domain logistics service, then delegates. Module routers call this module
(their own domain) which in turn delegates to the orders-domain implementation.
"""
from __future__ import annotations
from typing import Any
from sqlalchemy.orm import Session

# Raw implementations live in the orders-domain logistics service.
from domains.orders.services.logistics_service import (
    create_carrier as _ords_create_carrier,
    create_shipment as _ords_create_shipment,
    delete_carrier as _ords_delete_carrier,
    delete_shipping_zone as _ords_delete_shipping_zone,
    get_active_shipments as _ords_get_active_shipments,
    get_carriers as _ords_get_carriers,
    get_distribution_channels as _ords_get_distribution_channels,
    get_logistics_summary as _ords_get_logistics_summary,
    get_orders_to_fulfil as _ords_get_orders_to_fulfil,
    get_shipment_events as _ords_get_shipment_events,
    get_shipment_history as _ords_get_shipment_history,
    get_shipping_zones as _ords_get_shipping_zones,
    scan_shipment_event as _ords_scan_shipment_event,
    update_event_gps as _ords_update_event_gps,
    update_shipment_status as _ords_update_shipment_status,
    upsert_shipping_zone as _ords_upsert_shipping_zone,
)


def _user_dict(current_user: Any) -> dict:
    """Convert the authenticated User ORM object into the dict the orders service expects."""
    return {"id": current_user.id, "role": getattr(current_user, "role", None)}

async def get_logistics_summary(current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_logistics_summary(_user_dict(current_user), db)

async def get_carriers(current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_carriers(_user_dict(current_user), db)

async def create_carrier(data, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_create_carrier(data, _user_dict(current_user), db)

async def delete_carrier(carrier_id, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_delete_carrier(carrier_id, _user_dict(current_user), db)

async def get_shipping_zones(current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_shipping_zones(_user_dict(current_user), db)

async def upsert_shipping_zone(data, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_upsert_shipping_zone(data, _user_dict(current_user), db)

async def delete_shipping_zone(zone_id, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_delete_shipping_zone(zone_id, _user_dict(current_user), db)

async def get_orders_to_fulfil(current_user, db, limit=200, offset=0):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_orders_to_fulfil(_user_dict(current_user), db, limit, offset)

async def create_shipment(data, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_create_shipment(data, _user_dict(current_user), db)

async def get_active_shipments(current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_active_shipments(_user_dict(current_user), db)

async def get_shipment_history(current_user, db, page=1, per_page=30):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_shipment_history(_user_dict(current_user), db, page, per_page)

async def get_shipment_events(shipment_id, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_shipment_events(shipment_id, _user_dict(current_user), db)

async def scan_shipment_event(shipment_id, data, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_scan_shipment_event(shipment_id, data, _user_dict(current_user), db)

async def update_shipment_status(shipment_id, data, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_update_shipment_status(shipment_id, data, _user_dict(current_user), db)

async def update_event_gps(event_id, lat, lng, current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_update_event_gps(event_id, lat, lng, _user_dict(current_user), db)

async def get_distribution_channels(current_user, db):
    """Thin adapter: convert User -> dict, delegate to orders service."""
    return await _ords_get_distribution_channels(_user_dict(current_user), db)

