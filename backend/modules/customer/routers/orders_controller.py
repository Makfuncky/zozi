"""controllers.orders.orders_controller controller.

Business logic is delegated to services.orders.orders_service (routers -> controllers -> services)."""

from domains.orders.services.orders_service import _build_shipping_address
from domains.orders.services.orders_service import _build_supply_chain_timeline
from domains.orders.services.orders_service import _calculate_fallback_shipping
from domains.orders.services.orders_service import _calculate_order_amounts
from domains.orders.services.orders_service import _calculate_shipping
from domains.orders.services.orders_service import _calculate_supplier_zone_shipping
from domains.orders.services.orders_service import _events_for_order
from domains.orders.services.orders_service import _generate_order_number
from domains.orders.services.orders_service import _get_logistics_partner_for_user
from domains.orders.services.orders_service import _group_supplier_totals
from domains.orders.services.orders_service import _load_events_for_shipments
from domains.orders.services.orders_service import _load_products_for_order
from domains.orders.services.orders_service import _load_shipments_for_orders
from domains.orders.services.orders_service import _quote_supplier_groups
from domains.orders.services.orders_service import _resolve_destination_city
from domains.orders.services.orders_service import _resolve_destination_country
from domains.orders.services.orders_service import _resolve_order_level_logistics_fields
from domains.orders.services.orders_service import _save_customer_delivery_profile
from domains.orders.services.orders_service import _supplier_can_access_order
from domains.orders.services.orders_service import _zone_country_codes
from domains.orders.services.orders_service import cancel_order
from domains.orders.services.orders_service import confirm_order_receipt_scan
from domains.orders.services.orders_service import confirm_order_scan_receipt
from domains.orders.services.orders_service import create_order
from domains.orders.services.orders_service import get_order
from domains.orders.services.orders_service import get_order_invoice
from domains.orders.services.orders_service import get_order_tracking
from domains.orders.services.orders_service import get_orders
from domains.orders.services.orders_service import logger
from domains.orders.services.orders_service import preview_order
from domains.orders.services.orders_service import respond_to_shipment_confirmation

__all__ = [
    "_build_shipping_address", "_build_supply_chain_timeline", "_calculate_fallback_shipping", "_calculate_order_amounts", "_calculate_shipping", "_calculate_supplier_zone_shipping",
    "_events_for_order", "_generate_order_number", "_get_logistics_partner_for_user", "_group_supplier_totals", "_load_events_for_shipments", "_load_products_for_order",
    "_load_shipments_for_orders", "_quote_supplier_groups", "_resolve_destination_city", "_resolve_destination_country", "_resolve_order_level_logistics_fields", "_save_customer_delivery_profile",
    "_supplier_can_access_order", "_zone_country_codes", "cancel_order", "confirm_order_receipt_scan", "confirm_order_scan_receipt", "create_order",
    "get_order", "get_order_invoice", "get_order_tracking", "get_orders", "logger", "preview_order",
    "respond_to_shipment_confirmation"
]
