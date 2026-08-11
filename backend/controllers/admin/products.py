"""controllers.admin.products controller.

Business logic is delegated to services.admin.products_service (routers -> controllers -> services)."""

from services.admin.products_service import (
    _build_list_page_payload, _normalize_image_path, _product_to_dict, _variant_to_dict, approve_product, bulk_delete_products_admin,
    bulk_product_moderation, delete_product_admin, get_all_products, get_pending_products, reject_product, restore_product_admin,
    toggle_product_badge
)

__all__ = [
    "_build_list_page_payload", "_normalize_image_path", "_product_to_dict", "_variant_to_dict", "approve_product", "bulk_delete_products_admin",
    "bulk_product_moderation", "delete_product_admin", "get_all_products", "get_pending_products", "reject_product", "restore_product_admin",
    "toggle_product_badge"
]
