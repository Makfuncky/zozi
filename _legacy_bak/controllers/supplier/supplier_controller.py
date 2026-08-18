"""controllers.supplier.supplier_controller controller.

Business logic is delegated to services.supplier.supplier_service (routers -> controllers -> services)."""

from services.supplier.supplier_service import (
    ALLOWED_IMAGE_EXTS, CURRENT_TERMS_VERSION, MAX_BULK_PRODUCTS, MAX_IMAGE_SIZE, _AI_IMAGE_SMOKE_REPORT, _AI_IMAGE_SMOKE_SCRIPT,
    _ALLOWED_PROFILE_FIELDS, _BADGE_AMOUNT_QUANT, _BADGE_THRESHOLDS, _FULFILLED_ORDER_STATUSES, _MANUAL_BADGE_LEVELS, _PERIOD_DAYS,
    _PROFILE_JSON_ARRAY_FIELDS, _PROFILE_JSON_OBJECT_FIELDS, _PUBLIC_SUPPLIER_CACHE_TTL, _SUPPLIER_PROFILE_MEDIA_FIELDS, _UNSET, _VALID_BUSINESS_TYPES,
    _badge_for_score, _badge_period_bounds, _badge_tier_meets_metrics, _build_bulk_upload_error, _build_list_page_payload, _build_public_supplier_cache_key,
    _build_public_supplier_summary, _build_supplier_product_payload, _build_variant_title, _coerce_optional_bool, _compute_badge_threshold_metrics, _create_badge_billing_record,
    _deserialize_profile_json, _ensure_supplier_profile_record, _find_existing_badge_billing, _generate_variant_product_code, _get_public_supplier_aggregates, _get_public_supplier_record,
    _get_supplier_max_return_window_days, _load_active_badge_tiers, _load_shipments_for_orders, _load_supplier_ai_audit_summary, _load_users_by_ids, _map_bulk_upload_error,
    _maybe_create_recurring_badge_billing, _normalize_media_path, _normalize_optional_product_text, _normalize_product_video_reference, _normalize_product_visibility_regions, _normalize_supplier_lookup_token,
    _normalize_variant_attributes, _normalize_variant_axes, _parse_optional_datetime, _parse_optional_return_window_days, _parse_product_variants_payload, _parse_supplier_return_window_days,
    _persist_supplier_product, _process_image_with_tools, _product_code_segment, _public_storefront_visibility_clause, _public_supplier_slug, _replace_product_variants,
    _resolve_category_id, _round_badge_amount, _sanitize_profile_json, _sanitize_profile_string, _save_supplier_profile_media_upload, _save_upload,
    _select_eligible_badge_tier, _serialize_badge_billing_record, _serialize_product_variant, _serialize_product_visibility_regions, _serialize_profile_json, _serialize_supplier_profile,
    _slugify_supplier_storefront, _start_of_month, _start_of_next_month, _start_of_next_year, _start_of_year, _supplier_lookup_sql_expression,
    accept_supplier_terms, admin_set_supplier_badge, bulk_inventory_adjust, bulk_upload_products, compute_credibility_score, create_supplier_product,
    create_supplier_product_upload, delete_supplier_product, execute_bulk_operation, export_products_csv, get_inventory_alerts, get_payout_history,
    get_public_supplier_products, get_public_supplier_profile, get_supplier_analytics, get_supplier_analytics_timeseries, get_supplier_bank_account, get_supplier_inventory,
    get_supplier_label_payload, get_supplier_onboarding_status, get_supplier_order_detail, get_supplier_orders, get_supplier_product, get_supplier_products,
    get_supplier_profile, get_supplier_profile_business, get_supplier_regions, get_supplier_reports, get_supplier_shipments, import_products_csv,
    list_public_suppliers, list_supplier_badge_billing_history, list_supplier_badge_catalog, logger, process_product_image, purchase_supplier_badge,
    queue_supplier_ai_audit, record_badge_billing_payment, refresh_supplier_badge, request_payout, request_verification, resolve_public_supplier_slug,
    run_badge_recalculation_cycle, run_supplier_ai_audit, update_inventory_levels, update_product_stock, update_supplier_order_status, update_supplier_product,
    update_supplier_profile, update_supplier_profile_business, update_supplier_regions, upload_supplier_parcel_proof, upload_supplier_profile_business_media, upload_verification_documents,
    upsert_supplier_bank_account
)

__all__ = [
    "ALLOWED_IMAGE_EXTS", "CURRENT_TERMS_VERSION", "MAX_BULK_PRODUCTS", "MAX_IMAGE_SIZE", "_AI_IMAGE_SMOKE_REPORT", "_AI_IMAGE_SMOKE_SCRIPT",
    "_ALLOWED_PROFILE_FIELDS", "_BADGE_AMOUNT_QUANT", "_BADGE_THRESHOLDS", "_FULFILLED_ORDER_STATUSES", "_MANUAL_BADGE_LEVELS", "_PERIOD_DAYS",
    "_PROFILE_JSON_ARRAY_FIELDS", "_PROFILE_JSON_OBJECT_FIELDS", "_PUBLIC_SUPPLIER_CACHE_TTL", "_SUPPLIER_PROFILE_MEDIA_FIELDS", "_UNSET", "_VALID_BUSINESS_TYPES",
    "_badge_for_score", "_badge_period_bounds", "_badge_tier_meets_metrics", "_build_bulk_upload_error", "_build_list_page_payload", "_build_public_supplier_cache_key",
    "_build_public_supplier_summary", "_build_supplier_product_payload", "_build_variant_title", "_coerce_optional_bool", "_compute_badge_threshold_metrics", "_create_badge_billing_record",
    "_deserialize_profile_json", "_ensure_supplier_profile_record", "_find_existing_badge_billing", "_generate_variant_product_code", "_get_public_supplier_aggregates", "_get_public_supplier_record",
    "_get_supplier_max_return_window_days", "_load_active_badge_tiers", "_load_shipments_for_orders", "_load_supplier_ai_audit_summary", "_load_users_by_ids", "_map_bulk_upload_error",
    "_maybe_create_recurring_badge_billing", "_normalize_media_path", "_normalize_optional_product_text", "_normalize_product_video_reference", "_normalize_product_visibility_regions", "_normalize_supplier_lookup_token",
    "_normalize_variant_attributes", "_normalize_variant_axes", "_parse_optional_datetime", "_parse_optional_return_window_days", "_parse_product_variants_payload", "_parse_supplier_return_window_days",
    "_persist_supplier_product", "_process_image_with_tools", "_product_code_segment", "_public_storefront_visibility_clause", "_public_supplier_slug", "_replace_product_variants",
    "_resolve_category_id", "_round_badge_amount", "_sanitize_profile_json", "_sanitize_profile_string", "_save_supplier_profile_media_upload", "_save_upload",
    "_select_eligible_badge_tier", "_serialize_badge_billing_record", "_serialize_product_variant", "_serialize_product_visibility_regions", "_serialize_profile_json", "_serialize_supplier_profile",
    "_slugify_supplier_storefront", "_start_of_month", "_start_of_next_month", "_start_of_next_year", "_start_of_year", "_supplier_lookup_sql_expression",
    "accept_supplier_terms", "admin_set_supplier_badge", "bulk_inventory_adjust", "bulk_upload_products", "compute_credibility_score", "create_supplier_product",
    "create_supplier_product_upload", "delete_supplier_product", "execute_bulk_operation", "export_products_csv", "get_inventory_alerts", "get_payout_history",
    "get_public_supplier_products", "get_public_supplier_profile", "get_supplier_analytics", "get_supplier_analytics_timeseries", "get_supplier_bank_account", "get_supplier_inventory",
    "get_supplier_label_payload", "get_supplier_onboarding_status", "get_supplier_order_detail", "get_supplier_orders", "get_supplier_product", "get_supplier_products",
    "get_supplier_profile", "get_supplier_profile_business", "get_supplier_regions", "get_supplier_reports", "get_supplier_shipments", "import_products_csv",
    "list_public_suppliers", "list_supplier_badge_billing_history", "list_supplier_badge_catalog", "logger", "process_product_image", "purchase_supplier_badge",
    "queue_supplier_ai_audit", "record_badge_billing_payment", "refresh_supplier_badge", "request_payout", "request_verification", "resolve_public_supplier_slug",
    "run_badge_recalculation_cycle", "run_supplier_ai_audit", "update_inventory_levels", "update_product_stock", "update_supplier_order_status", "update_supplier_product",
    "update_supplier_profile", "update_supplier_profile_business", "update_supplier_regions", "upload_supplier_parcel_proof", "upload_supplier_profile_business_media", "upload_verification_documents",
    "upsert_supplier_bank_account"
]
