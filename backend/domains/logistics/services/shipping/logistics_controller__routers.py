"""controllers.orders.logistics_controller controller.

Business logic is delegated to services.orders.logistics_service (routers -> controllers -> services)."""

from domains.orders.services.logistics_service import (
    EVENT_TO_STATUS, SHIPMENT_STATUSES, _allowed_scan_codes, _apply_package_metadata, _create_shipment_event, _parse_optional_datetime,
    _parse_optional_nonnegative_float, _parse_optional_positive_int, _publish_supplier_shipment_update, _require_supplier, _resolve_assigned_partner, _serialize_carrier,
    _serialize_event, _serialize_shipment, _serialize_zone, create_carrier, create_shipment, delete_carrier,
    delete_shipping_zone, get_active_shipments, get_carriers, get_distribution_channels, get_logistics_summary, get_orders_to_fulfil,
    get_shipment_events, get_shipment_history, get_shipping_zones, logger, scan_shipment_event, update_event_gps,
    update_shipment_status, upsert_shipping_zone
)

__all__ = [
    "EVENT_TO_STATUS", "SHIPMENT_STATUSES", "_allowed_scan_codes", "_apply_package_metadata", "_create_shipment_event", "_parse_optional_datetime",
    "_parse_optional_nonnegative_float", "_parse_optional_positive_int", "_publish_supplier_shipment_update", "_require_supplier", "_resolve_assigned_partner", "_serialize_carrier",
    "_serialize_event", "_serialize_shipment", "_serialize_zone", "create_carrier", "create_shipment", "delete_carrier",
    "delete_shipping_zone", "get_active_shipments", "get_carriers", "get_distribution_channels", "get_logistics_summary", "get_orders_to_fulfil",
    "get_shipment_events", "get_shipment_history", "get_shipping_zones", "logger", "scan_shipment_event", "update_event_gps",
    "update_shipment_status", "upsert_shipping_zone"
]
