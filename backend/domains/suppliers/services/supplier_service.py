"""Supplier service — backward-compatible shim.

Code has been moved to:
   - supplier_shared: constants and helper functions
   - profile/supplier_profile: profile management
   - products/supplier_products: product management
   - orders/supplier_orders: order management
   - health/supplier_health: health scoring, analytics, badge, public, bank
"""
from domains.suppliers.services.supplier_shared import *  # noqa: F401,F403
from domains.suppliers.services.profile.supplier_profile import *  # noqa: F401,F403
from domains.suppliers.services.products.supplier_products import *  # noqa: F401,F403
from domains.suppliers.services.orders.supplier_orders import *  # noqa: F401,F403
from domains.suppliers.services.health.supplier_health import *  # noqa: F401,F403

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
    "create_supplier_product",
    "create_supplier_product_upload",
    "update_supplier_product",
    "delete_supplier_product",
    "export_products_csv",
    "import_products_csv",
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
