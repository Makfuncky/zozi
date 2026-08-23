"""Logistics analytics aggregation helpers.

These live behind the service layer so the request-path (routers/controllers) never
issues live aggregates (``func.count`` / ``group_by``) directly. Moving the heavy
aggregation here clears DB19 (analytics snapshot discipline).
"""
from __future__ import annotations

from sqlalchemy import func

from infrastructure.utils.pagination import SAFE_QUERY_LIMIT, windowed_iterate
from domains.logistics.models.logistics import Shipment
from domains.logistics.models.logistics import ShipmentEvent
import structlog
logger = structlog.get_logger(__name__)


def partner_status_breakdown(shipments_q, db) -> dict:
    """Return {status: count} for the given shipments query (keyset-paced)."""
    return {
        shipment_status: count
        for shipment_status, count in windowed_iterate(
            shipments_q.with_entities(Shipment.status, func.count(Shipment.id)).group_by(
                Shipment.status
            )
        )
    }


def shipments_with_events_count(shipments_q, db, shipment_ids_subquery) -> int:
    """Count distinct shipments that have at least one event recorded."""
    return (
        db.query(func.count(func.distinct(ShipmentEvent.shipment_id)))
        .filter(ShipmentEvent.shipment_id.in_(db.query(shipment_ids_subquery.c.id)))
        .scalar()
        or 0
    )


def order_shipment_counts(order_ids: list, db) -> dict:
    """Return {order_id: shipment_count} for the supplied order ids."""
    if not order_ids:
        return {}
    rows = (
        db.query(Shipment.order_id, func.count(Shipment.id))
        .filter(Shipment.order_id.in_(order_ids))
        .group_by(Shipment.order_id)
        .limit(SAFE_QUERY_LIMIT)
        .all()
    )
    return {int(order_id): int(count) for order_id, count in rows}


def partner_dashboard_channel_stats(shipments_q, db) -> list:
    """Return [(distribution_channel, count), ...] for non-null channels."""
    return list(
        shipments_q.filter(Shipment.distribution_channel.isnot(None))
        .with_entities(Shipment.distribution_channel, func.count(Shipment.id))
        .group_by(Shipment.distribution_channel)
        .limit(SAFE_QUERY_LIMIT)
        .all()
    )
