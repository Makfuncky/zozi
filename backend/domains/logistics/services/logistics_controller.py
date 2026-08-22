"""controllers.orders.logistics_controller controller.

Business logic is delegated to services.orders.logistics_service (routers -> controllers -> services)."""

from domains.logistics.services.logistics_service import EVENT_TO_STATUS
from domains.logistics.services.logistics_service import SHIPMENT_STATUSES
from domains.logistics.services.logistics_service import _allowed_scan_codes
from domains.logistics.services.logistics_service import _apply_package_metadata
from domains.logistics.services.logistics_service import _create_shipment_event
from domains.logistics.services.logistics_service import _parse_optional_datetime
from domains.logistics.services.logistics_service import _parse_optional_nonnegative_float
from domains.logistics.services.logistics_service import _parse_optional_positive_int
from domains.logistics.services.logistics_service import _publish_supplier_shipment_update
from domains.logistics.services.logistics_service import _require_supplier
from domains.logistics.services.logistics_service import _resolve_assigned_partner
from domains.logistics.services.logistics_service import _serialize_carrier
from domains.logistics.services.logistics_service import _serialize_event
from domains.logistics.services.logistics_service import _serialize_shipment
from domains.logistics.services.logistics_service import _serialize_zone
from domains.logistics.services.logistics_service import create_carrier
from domains.logistics.services.logistics_service import create_shipment
from domains.logistics.services.logistics_service import delete_carrier
from domains.logistics.services.logistics_service import delete_shipping_zone
from domains.logistics.services.logistics_service import get_active_shipments
from domains.logistics.services.logistics_service import get_carriers
from domains.logistics.services.logistics_service import get_distribution_channels
from domains.logistics.services.logistics_service import get_logistics_summary
from domains.logistics.services.logistics_service import get_orders_to_fulfil
from domains.logistics.services.logistics_service import get_shipment_events
from domains.logistics.services.logistics_service import get_shipment_history
from domains.logistics.services.logistics_service import get_shipping_zones
from domains.logistics.services.logistics_service import logger
from domains.logistics.services.logistics_service import scan_shipment_event
from domains.logistics.services.logistics_service import update_event_gps
from domains.logistics.services.logistics_service import update_shipment_status
from domains.logistics.services.logistics_service import upsert_shipping_zone

__all__ = [
    "EVENT_TO_STATUS", "SHIPMENT_STATUSES", "_allowed_scan_codes", "_apply_package_metadata", "_create_shipment_event", "_parse_optional_datetime",
    "_parse_optional_nonnegative_float", "_parse_optional_positive_int", "_publish_supplier_shipment_update", "_require_supplier", "_resolve_assigned_partner", "_serialize_carrier",
    "_serialize_event", "_serialize_shipment", "_serialize_zone", "create_carrier", "create_shipment", "delete_carrier",
    "delete_shipping_zone", "get_active_shipments", "get_carriers", "get_distribution_channels", "get_logistics_summary", "get_orders_to_fulfil",
    "get_shipment_events", "get_shipment_history", "get_shipping_zones", "logger", "scan_shipment_event", "update_event_gps",
    "update_shipment_status", "upsert_shipping_zone"
]
