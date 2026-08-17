"""controllers.orders.orders_controller controller.

Business logic is delegated to services.orders.orders_service (routers -> controllers -> services)."""

from services.orders.orders_service import (
    _build_shipping_address, _build_supply_chain_timeline, _calculate_fallback_shipping, _calculate_order_amounts, _calculate_shipping, _calculate_supplier_zone_shipping,
    _events_for_order, _generate_order_number, _get_logistics_partner_for_user, _group_supplier_totals, _load_events_for_shipments, _load_products_for_order,
    _load_shipments_for_orders, _quote_supplier_groups, _resolve_destination_city, _resolve_destination_country, _resolve_order_level_logistics_fields, _save_customer_delivery_profile,
    _supplier_can_access_order, _zone_country_codes, cancel_order, confirm_order_receipt_scan, confirm_order_scan_receipt, create_order,
    get_order, get_order_invoice, get_order_tracking, get_orders, logger, preview_order,
    respond_to_shipment_confirmation
)

__all__ = [
    "_build_shipping_address", "_build_supply_chain_timeline", "_calculate_fallback_shipping", "_calculate_order_amounts", "_calculate_shipping", "_calculate_supplier_zone_shipping",
    "_events_for_order", "_generate_order_number", "_get_logistics_partner_for_user", "_group_supplier_totals", "_load_events_for_shipments", "_load_products_for_order",
    "_load_shipments_for_orders", "_quote_supplier_groups", "_resolve_destination_city", "_resolve_destination_country", "_resolve_order_level_logistics_fields", "_save_customer_delivery_profile",
    "_supplier_can_access_order", "_zone_country_codes", "cancel_order", "confirm_order_receipt_scan", "confirm_order_scan_receipt", "create_order",
    "get_order", "get_order_invoice", "get_order_tracking", "get_orders", "logger", "preview_order",
    "respond_to_shipment_confirmation"
]
