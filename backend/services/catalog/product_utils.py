"""
Product Catalog Utilities — variant resolution and cache versioning.

Canonical home for product-related utilities that were previously scattered
in controllers/products_controller.py. Other controllers and routers now
import from here instead of crossing the controller→controller boundary.
"""

import hashlib
import json
import logging
from typing import Any, Optional

from data.models import Product, ProductVariant

logger = logging.getLogger(__name__)

_PRODUCT_CACHE_VERSION_KEY = "products:cache:version"


def _normalize_variant_selector(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def _attribute_values(variant: ProductVariant) -> list[str]:
    raw = getattr(variant, "attributes_json", None)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, dict):
        return []
    return [str(v).strip().lower() for v in parsed.values() if str(v).strip()]


def resolve_product_variant(
    product: Product,
    selected_size: Optional[str],
    selected_color: Optional[str],
) -> Optional[ProductVariant]:
    """Resolve a product variant from size/color selectors."""
    variants = list(getattr(product, "variants", []) or [])
    if not variants:
        return None

    normalized_size = _normalize_variant_selector(selected_size)
    normalized_color = _normalize_variant_selector(selected_color)
    if not normalized_size and not normalized_color:
        return None

    for variant in variants:
        if not getattr(variant, "is_active", True):
            continue
        variant_size = _normalize_variant_selector(getattr(variant, "size", None))
        variant_color = _normalize_variant_selector(getattr(variant, "color", None))
        variant_title = _normalize_variant_selector(getattr(variant, "title", None))
        attribute_values = _attribute_values(variant)

        color_matches = not normalized_color or normalized_color == variant_color or normalized_color in attribute_values
        size_matches = not normalized_size or normalized_size in {variant_size, variant_title} or normalized_size in attribute_values
        if color_matches and size_matches:
            return variant

    return None


def _bump_product_cache_version() -> None:
    """Increment the product cache version in Redis."""
    try:
        from utils.cache import _get_redis_client
        redis_client = _get_redis_client()
        if redis_client is not None:
            redis_client.incr(_PRODUCT_CACHE_VERSION_KEY)
    except Exception:
        pass


def _build_product_cache_key(prefix: str, payload: dict[str, Any]) -> str:
    from utils.cache import _get_product_cache_version
    version = _get_product_cache_version()
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"products:{prefix}:v{version}:{digest}"
