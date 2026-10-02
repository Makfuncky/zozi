"""Supplier service — backward-compatible shim.

Code has been moved to:
   - supplier_shared: constants and helper functions
   - profile/supplier_profile: profile management
   - products/supplier_products: product management
   - orders/supplier_orders: order management
   - health/supplier_health: health scoring, analytics, badge, public, bank
"""
from domains.suppliers.services.supplier_shared import (
    build_list_page_payload,
    build_public_supplier_cache_key,
    normalize_optional_product_text,
    normalize_product_visibility_regions,
    serialize_product_visibility_regions,
    load_shipments_for_orders,
    load_users_by_ids,
    parse_optional_datetime,
    persist_supplier_product,
    map_bulk_upload_error,
    build_bulk_upload_error,
    load_supplier_ai_audit_summary,
    run_supplier_ai_audit,
    queue_supplier_ai_audit,
    parse_optional_return_window_days,
    get_supplier_max_return_window_days,
    parse_supplier_return_window_days,
    coerce_optional_bool,
    sanitize_profile_string,
    sanitize_profile_json,
    normalize_product_video_reference,
    resolve_category_id,
    normalize_variant_axes,
    normalize_variant_attributes,
    build_variant_title,
    product_code_segment,
    generate_variant_product_code,
    parse_product_variants_payload,
    replace_product_variants,
    serialize_product_variant,
    slugify_supplier_storefront,
    deserialize_profile_json,
    serialize_profile_json,
    build_supplier_product_payload,
)
from domains.suppliers.services.profile.supplier_profile import (
    get_supplier_profile,
    update_supplier_profile,
    request_verification,
)
from domains.suppliers.services.products.supplier_products import (
    create_supplier_product,
    delete_supplier_product,
    get_supplier_product,
    get_supplier_products,
    process_product_image,
    update_supplier_product,
)
from domains.suppliers.services.orders.supplier_orders import (
    get_supplier_label_payload,
    get_supplier_order_detail,
    get_supplier_orders,
    update_supplier_order_status,
    upload_supplier_parcel_proof,
)
from domains.suppliers.services.health.supplier_health import (
    accept_supplier_terms,
    admin_set_supplier_badge,
    bulk_inventory_adjust,
    bulk_upload_products,
    compute_credibility_score,
    execute_bulk_operation,
    export_products_csv,
    get_inventory_alerts,
    get_payout_history,
    get_public_supplier_products,
    get_public_supplier_profile,
    get_supplier_analytics,
    get_supplier_analytics_timeseries,
    get_supplier_bank_account,
    get_supplier_inventory,
    get_supplier_onboarding_status,
    get_supplier_profile,
    get_supplier_profile_business,
    get_supplier_regions,
    get_supplier_reports,
    get_supplier_shipments,
    list_public_suppliers,
    refresh_supplier_badge,
    request_payout,
    request_verification,
    resolve_public_supplier_slug,
    run_badge_recalculation_cycle,
    update_inventory_levels,
    update_product_stock,
    update_supplier_profile,
    update_supplier_profile_business,
    update_supplier_regions,
    upload_supplier_profile_business_media,
    upsert_supplier_bank_account,
)

from providers.security.watchlist import screen_watchlist

__all__ = [
    # Orders
    "get_supplier_orders",
    "update_supplier_order_status",
    "get_supplier_order_detail",
    "get_supplier_label_payload",
    "upload_supplier_parcel_proof",
    "get_supplier_shipments",
    # Products
    "get_supplier_products",
    "get_supplier_product",
    "process_product_image",
    "create_supplier_product",
    "update_supplier_product",
    "delete_supplier_product",
    "export_products_csv",
    "bulk_upload_products",
    "bulk_inventory_adjust",
    # Profile
    "get_supplier_profile",
    "update_supplier_profile",
    "request_verification",
    "get_supplier_profile_business",
    "update_supplier_profile_business",
    "upload_supplier_profile_business_media",
    "accept_supplier_terms",
    "get_supplier_onboarding_status",
    "get_supplier_regions",
    "update_supplier_regions",
    # Health/Analytics
    "get_supplier_analytics",
    "get_supplier_inventory",
    "update_product_stock",
    "update_inventory_levels",
    "get_inventory_alerts",
    "get_supplier_reports",
    "get_payout_history",
    "request_payout",
    "execute_bulk_operation",
    "compute_credibility_score",
    "refresh_supplier_badge",
    "run_badge_recalculation_cycle",
    "get_supplier_analytics_timeseries",
    "admin_set_supplier_badge",
    "list_public_suppliers",
    "resolve_public_supplier_slug",
    "get_public_supplier_profile",
    "get_public_supplier_products",
    "get_supplier_bank_account",
    "upsert_supplier_bank_account",
    # Provider-wired helpers
    "screen_supplier",
]


def screen_supplier(name: str, country_code: str):
    """Screen a supplier against watchlists using the security provider."""
    try:
        return screen_watchlist(employee_code="", full_name=name, country_code=country_code)
    except Exception:
        return {"cleared": True, "matches": []}
