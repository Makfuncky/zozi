"""controllers.products.products_controller controller.

Business logic is delegated to services.products.products_service (routers -> controllers -> services)."""

from services.products.products_service import (
    _CATEGORY_LOOKUP_ALIASES, _LOW_STOCK_THRESHOLD, _MONEY_QUANT, _PRODUCT_CACHE_VERSION_KEY, _PRODUCT_DETAIL_CACHE_TTL, _PRODUCT_LIST_CACHE_TTL,
    _PUBLIC_PRODUCTS_CACHE_CONTROL, _apply_live_offer_metadata, _build_product_cache_key, _bump_product_cache_version, _cache_get_json, _cache_set_json,
    _category_lookup_tokens, _get_active_flash_sales, _get_product_cache_version, _get_redis_client, _is_product_restricted_for_country, _list_products_cached,
    _normalize_datetime, _normalize_product_visibility_regions, _normalize_variant_selector, _parse_flash_sale_product_ids, _prepare_product_write_payload, _resolve_product_category_fields,
    _serialize_product, _serialize_products, autocomplete_products, create_product, create_supplier_product_with_upload, delete_product,
    get_product, get_product_by_barcode, get_products, get_recommended_products, get_supplier_names, get_supplier_products_simple,
    logger, patch_product_stock, resolve_product_variant, update_product, update_product_return_window
)

__all__ = [
    "_CATEGORY_LOOKUP_ALIASES", "_LOW_STOCK_THRESHOLD", "_MONEY_QUANT", "_PRODUCT_CACHE_VERSION_KEY", "_PRODUCT_DETAIL_CACHE_TTL", "_PRODUCT_LIST_CACHE_TTL",
    "_PUBLIC_PRODUCTS_CACHE_CONTROL", "_apply_live_offer_metadata", "_build_product_cache_key", "_bump_product_cache_version", "_cache_get_json", "_cache_set_json",
    "_category_lookup_tokens", "_get_active_flash_sales", "_get_product_cache_version", "_get_redis_client", "_is_product_restricted_for_country", "_list_products_cached",
    "_normalize_datetime", "_normalize_product_visibility_regions", "_normalize_variant_selector", "_parse_flash_sale_product_ids", "_prepare_product_write_payload", "_resolve_product_category_fields",
    "_serialize_product", "_serialize_products", "autocomplete_products", "create_product", "create_supplier_product_with_upload", "delete_product",
    "get_product", "get_product_by_barcode", "get_products", "get_recommended_products", "get_supplier_names", "get_supplier_products_simple",
    "logger", "patch_product_stock", "resolve_product_variant", "update_product", "update_product_return_window"
]
