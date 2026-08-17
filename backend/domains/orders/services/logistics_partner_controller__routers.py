"""controllers.orders.logistics_partner_controller controller.

Business logic is delegated to services.orders.logistics_partner_service (routers -> controllers -> services)."""

from domains.orders.services.logistics_partner_service import (
    ACTIVE_SHIPMENT_STATUSES, ALLOWED_LP_DOC_TYPES, ANALYTICS_LOOKBACK_DAYS, CURRENT_LOGISTICS_TERMS_VERSION, PARTNER_HIDDEN_STATUS, PARTNER_PICKUP_READY_STATUS,
    PARTNER_VISIBLE_ASSIGNED_STATUSES, SLA_ALERT_STATUSES, _PARTNER_DELETE_BLOCKING_MODELS, _active_confirmation_map, _apply_delivery_signature, _build_live_locations,
    _build_partner_delete_blocker, _build_route_plan, _calculate_partner_analytics, _calculate_partner_payout_summary, _collect_sla_alerts, _ensure_sla_notifications,
    _extract_delivery_signature, _filter_partner_analytics_period, _format_compound_location, _get_partner_for_user, _haversine_km, _is_pickup_ready,
    _is_shipment_visible_to_partner, _latest_geo_events_for_shipments, _next_partner_code, _notify_partner_transition, _order_shipment_counts, _parse_category_pricing_rule_payload,
    _parse_optional_service_area_id, _parse_partner_service_area_payload, _parse_partner_social_links, _parse_pricing_profile_payload, _parse_vehicle_rule_payload, _partner_api_status,
    _partner_dashboard_shipments_query, _partner_is_active, _partner_visible_shipments_query, _pickup_visible_to_partner, _publish_shipment_update, _require_admin,
    _resolve_partner_user_link, _sanitize_optional_string, _scoped_shipments_query, _serialize_city_distance, _serialize_lp_doc, _serialize_partner,
    _serialize_partner_analytics_payload, _serialize_partner_payout, _shipment_effective_pricing_breakdown, _shipment_logistics_allocation, _shipment_partner_revenue, _shipment_pickup_details,
    _status_display, _utcnow, _validate_partner_service_area, accept_partner_terms, admin_review_lp_document, bulk_manage_partners,
    bulk_update_shipment_status_partner, create_city_distance, create_partner, create_shipment_confirmation_request_partner, delete_city_distance, delete_my_partner_category_rule,
    delete_my_partner_pricing_profile, delete_my_partner_service_area, delete_my_partner_vehicle_rule, delete_partner, delete_partner_document, get_my_partner_profile,
    get_partner_analytics, get_partner_bank_account, get_partner_dashboard, get_partner_payouts, get_partner_pricing_insights, get_partner_shipments,
    get_public_partner, list_city_distances, list_my_partner_category_rules, list_my_partner_pricing_profiles, list_my_partner_service_areas, list_my_partner_vehicle_rules,
    list_partner_cod_remittance_receipts, list_partner_documents, list_partners, list_pending_partner_payouts, list_public_partners, logger,
    request_partner_payout, review_partner_category_rule, review_partner_pricing_profile, review_partner_profile, review_partner_service_area, review_partner_vehicle_rule,
    scan_lookup_shipment_partner, shipping_quote_for_customer, submit_partner_profile_for_review, update_city_distance, update_my_partner_profile, update_partner,
    update_shipment_status_partner, upload_partner_cod_remittance_receipt, upload_partner_document, upsert_my_partner_category_rule, upsert_my_partner_pricing_profile, upsert_my_partner_service_area,
    upsert_my_partner_vehicle_rule, upsert_partner_bank_account, verify_partner_payout
)

__all__ = [
    "ACTIVE_SHIPMENT_STATUSES", "ALLOWED_LP_DOC_TYPES", "ANALYTICS_LOOKBACK_DAYS", "CURRENT_LOGISTICS_TERMS_VERSION", "PARTNER_HIDDEN_STATUS", "PARTNER_PICKUP_READY_STATUS",
    "PARTNER_VISIBLE_ASSIGNED_STATUSES", "SLA_ALERT_STATUSES", "_PARTNER_DELETE_BLOCKING_MODELS", "_active_confirmation_map", "_apply_delivery_signature", "_build_live_locations",
    "_build_partner_delete_blocker", "_build_route_plan", "_calculate_partner_analytics", "_calculate_partner_payout_summary", "_collect_sla_alerts", "_ensure_sla_notifications",
    "_extract_delivery_signature", "_filter_partner_analytics_period", "_format_compound_location", "_get_partner_for_user", "_haversine_km", "_is_pickup_ready",
    "_is_shipment_visible_to_partner", "_latest_geo_events_for_shipments", "_next_partner_code", "_notify_partner_transition", "_order_shipment_counts", "_parse_category_pricing_rule_payload",
    "_parse_optional_service_area_id", "_parse_partner_service_area_payload", "_parse_partner_social_links", "_parse_pricing_profile_payload", "_parse_vehicle_rule_payload", "_partner_api_status",
    "_partner_dashboard_shipments_query", "_partner_is_active", "_partner_visible_shipments_query", "_pickup_visible_to_partner", "_publish_shipment_update", "_require_admin",
    "_resolve_partner_user_link", "_sanitize_optional_string", "_scoped_shipments_query", "_serialize_city_distance", "_serialize_lp_doc", "_serialize_partner",
    "_serialize_partner_analytics_payload", "_serialize_partner_payout", "_shipment_effective_pricing_breakdown", "_shipment_logistics_allocation", "_shipment_partner_revenue", "_shipment_pickup_details",
    "_status_display", "_utcnow", "_validate_partner_service_area", "accept_partner_terms", "admin_review_lp_document", "bulk_manage_partners",
    "bulk_update_shipment_status_partner", "create_city_distance", "create_partner", "create_shipment_confirmation_request_partner", "delete_city_distance", "delete_my_partner_category_rule",
    "delete_my_partner_pricing_profile", "delete_my_partner_service_area", "delete_my_partner_vehicle_rule", "delete_partner", "delete_partner_document", "get_my_partner_profile",
    "get_partner_analytics", "get_partner_bank_account", "get_partner_dashboard", "get_partner_payouts", "get_partner_pricing_insights", "get_partner_shipments",
    "get_public_partner", "list_city_distances", "list_my_partner_category_rules", "list_my_partner_pricing_profiles", "list_my_partner_service_areas", "list_my_partner_vehicle_rules",
    "list_partner_cod_remittance_receipts", "list_partner_documents", "list_partners", "list_pending_partner_payouts", "list_public_partners", "logger",
    "request_partner_payout", "review_partner_category_rule", "review_partner_pricing_profile", "review_partner_profile", "review_partner_service_area", "review_partner_vehicle_rule",
    "scan_lookup_shipment_partner", "shipping_quote_for_customer", "submit_partner_profile_for_review", "update_city_distance", "update_my_partner_profile", "update_partner",
    "update_shipment_status_partner", "upload_partner_cod_remittance_receipt", "upload_partner_document", "upsert_my_partner_category_rule", "upsert_my_partner_pricing_profile", "upsert_my_partner_service_area",
    "upsert_my_partner_vehicle_rule", "upsert_partner_bank_account", "verify_partner_payout"
]
