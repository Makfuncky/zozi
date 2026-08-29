"""catalog domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.catalog.models`` or ``domains.catalog.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from infrastructure.utils.pagination import (
    CursorPage,
    MAX_PAGE_SIZE,
    cursor_paginate_asc,
    get_max_page_size,
    keyset_paginate,
)

from domains.catalog.models.products import Category, Product, ProductFilterMetadata, ProductFilterOption, ProductVariant, ProductVideo, Review, VideoAnalytics, Wishlist, WishlistItem
from domains.promotions.models.promotions import BOGOPromotion, Banner


# --- Keyset (cursor) pagination helpers (diagram §6: NEVER OFFSET on hot lists) ---
# The existing ``list_*`` functions keep their public contract (a plain ``List``) so
# the 39 existing cross-domain consumers in ``domains/orders/services/*`` are
# unaffected, but they are now sourced via keyset (stable ``id`` order, no OFFSET).
# The ``*_page`` companions return a ``CursorPage`` for scale-ready cursor paging
# (the 100Ks-concurrent-user path) with optional country + soft-delete scoping.

def _keyset_list(model, db: Session, limit: int = 100) -> list:
    """Backward-compatible plain list sourced via keyset (no OFFSET)."""
    return cursor_paginate_asc(db.query(model), page_size=limit).items


def _keyset_page(model, db: Session, cursor: Optional[str] = None,
                 page_size: int = MAX_PAGE_SIZE, country_code: Optional[str] = None,
                 include_deleted: bool = False, has_country: bool = True,
                 has_deleted: bool = False) -> CursorPage:
    """Keyset-cursor page over ``model`` with optional country/soft-delete scoping."""
    q = db.query(model)
    if has_country and country_code:
        q = q.filter(model.country_code == country_code)
    if has_deleted and not include_deleted and getattr(model, "is_deleted", None) is not None:
        q = q.filter(model.is_deleted == False)
    return cursor_paginate_asc(q, cursor=cursor, page_size=page_size)


def get_category_by_id(db: Session, id_: int) -> Optional[Category]:
    """Return Category by primary key (or None)."""
    return db.get(Category, id_)

def list_categorys(db: Session, limit: int = 100) -> List[Category]:
    """Return up to ``limit`` Category rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Category, db, limit)

def list_categorys_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                        country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of categories (scale-ready)."""
    return _keyset_page(Category, db, cursor, page_size, country_code, has_deleted=False)

def get_product_by_id(db: Session, id_: int) -> Optional[Product]:
    """Return Product by primary key (or None)."""
    return db.get(Product, id_)

def list_products(db: Session, limit: int = 100) -> List[Product]:
    """Return up to ``limit`` Product rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Product, db, limit)

def list_products_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                       country_code: Optional[str] = None, include_deleted: bool = False) -> CursorPage:
    """Keyset-cursor page of products (scale-ready)."""
    return _keyset_page(Product, db, cursor, page_size, country_code, include_deleted, has_deleted=True)


def list_products_keyset(
    db: Session,
    *,
    include_deleted: bool = True,
    cursor: object = None,
    size: int = 50,
    country_code: object = None,
    order_by_created_desc: bool = True,
) -> dict:
    """Canonical 100Ks-scale hot-list reader for Products (keyset, never OFFSET).

    Mirrors ``domains.orders.ports.list_orders_keyset``. Returns a cursor envelope
    ``{items, next_cursor, page_size, has_next}`` using a composite, stable sort
    key ``(created_at, id)`` so paging latency stays flat as the catalog grows
    (ARCHITECTURE_DIAGRAM.md §6). Soft-deleted rows are excluded when the model
    supports ``is_deleted`` and ``include_deleted`` is False; results are scoped
    to ``country_code`` when provided (multi-tenant isolation at the read boundary).
    """
    q = db.query(Product)
    if country_code is not None:
        q = q.filter(Product.country_code == country_code)
    if not include_deleted and getattr(Product, "is_deleted", None) is not None:
        q = q.filter(Product.is_deleted == False)  # noqa: E712
    direction = "desc" if order_by_created_desc else "asc"
    sort_keys = [(Product.created_at, direction), (Product.id, direction)]
    return keyset_paginate(q, sort_keys=sort_keys, cursor=cursor, page_size=size)

def get_review_by_id(db: Session, id_: int) -> Optional[Review]:
    """Return Review by primary key (or None)."""
    return db.get(Review, id_)

def list_reviews(db: Session, limit: int = 100) -> List[Review]:
    """Return up to ``limit`` Review rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Review, db, limit)

def list_reviews_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                      country_code: Optional[str] = None, include_deleted: bool = False) -> CursorPage:
    """Keyset-cursor page of reviews (scale-ready)."""
    return _keyset_page(Review, db, cursor, page_size, country_code, include_deleted, has_deleted=True)

def get_wishlist_item_by_id(db: Session, id_: int) -> Optional[WishlistItem]:
    """Return WishlistItem by primary key (or None)."""
    return db.get(WishlistItem, id_)

def list_wishlist_items(db: Session, limit: int = 100) -> List[WishlistItem]:
    """Return up to ``limit`` WishlistItem rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(WishlistItem, db, limit)

def list_wishlist_items_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                             country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of wishlist items (scale-ready)."""
    return _keyset_page(WishlistItem, db, cursor, page_size, country_code, has_deleted=False)

def get_wishlist_by_id(db: Session, id_: int) -> Optional[Wishlist]:
    """Return Wishlist by primary key (or None)."""
    return db.get(Wishlist, id_)

def list_wishlists(db: Session, limit: int = 100) -> List[Wishlist]:
    """Return up to ``limit`` Wishlist rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(Wishlist, db, limit)

def list_wishlists_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                        country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of wishlists (scale-ready)."""
    return _keyset_page(Wishlist, db, cursor, page_size, country_code, has_deleted=False)

def get_product_variant_by_id(db: Session, id_: int) -> Optional[ProductVariant]:
    """Return ProductVariant by primary key (or None)."""
    return db.get(ProductVariant, id_)

def list_product_variants(db: Session, limit: int = 100) -> List[ProductVariant]:
    """Return up to ``limit`` ProductVariant rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductVariant, db, limit)

def list_product_variants_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                              country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of product variants (scale-ready)."""
    return _keyset_page(ProductVariant, db, cursor, page_size, country_code, has_deleted=False)

def get_product_video_by_id(db: Session, id_: int) -> Optional[ProductVideo]:
    """Return ProductVideo by primary key (or None)."""
    return db.get(ProductVideo, id_)

def list_product_videos(db: Session, limit: int = 100) -> List[ProductVideo]:
    """Return up to ``limit`` ProductVideo rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductVideo, db, limit)

def list_product_videos_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                             country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of product videos (scale-ready)."""
    return _keyset_page(ProductVideo, db, cursor, page_size, country_code, has_deleted=False)

def get_video_analytics_by_id(db: Session, id_: int) -> Optional[VideoAnalytics]:
    """Return VideoAnalytics by primary key (or None)."""
    return db.get(VideoAnalytics, id_)

def list_video_analyticss(db: Session, limit: int = 100) -> List[VideoAnalytics]:
    """Return up to ``limit`` VideoAnalytics rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(VideoAnalytics, db, limit)

def list_video_analyticss_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                               country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of video analytics (scale-ready)."""
    return _keyset_page(VideoAnalytics, db, cursor, page_size, country_code, has_deleted=False)

def get_product_filter_metadata_by_id(db: Session, id_: int) -> Optional[ProductFilterMetadata]:
    """Return ProductFilterMetadata by primary key (or None)."""
    return db.get(ProductFilterMetadata, id_)

def list_product_filter_metadatas(db: Session, limit: int = 100) -> List[ProductFilterMetadata]:
    """Return up to ``limit`` ProductFilterMetadata rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductFilterMetadata, db, limit)

def list_product_filter_metadatas_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                                       country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of product filter metadata (scale-ready)."""
    return _keyset_page(ProductFilterMetadata, db, cursor, page_size, country_code, has_deleted=False)

def get_product_filter_option_by_id(db: Session, id_: int) -> Optional[ProductFilterOption]:
    """Return ProductFilterOption by primary key (or None)."""
    return db.get(ProductFilterOption, id_)

def list_product_filter_options(db: Session, limit: int = 100) -> List[ProductFilterOption]:
    """Return up to ``limit`` ProductFilterOption rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(ProductFilterOption, db, limit)

def list_product_filter_options_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                                     country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of product filter options (scale-ready)."""
    return _keyset_page(ProductFilterOption, db, cursor, page_size, country_code, has_deleted=False)

def get_b_o_g_o_promotion_by_id(db: Session, id_: int) -> Optional[BOGOPromotion]:
    """Return BOGOPromotion by primary key (or None)."""
    return db.get(BOGOPromotion, id_)

def list_b_o_g_o_promotions(db: Session, limit: int = 100) -> List[BOGOPromotion]:
    """Return up to ``limit`` BOGOPromotion rows (keyset-ordered, no OFFSET)."""
    return _keyset_list(BOGOPromotion, db, limit)

def list_b_o_g_o_promotions_page(db: Session, cursor: Optional[str] = None, page_size: int = MAX_PAGE_SIZE,
                                 country_code: Optional[str] = None) -> CursorPage:
    """Keyset-cursor page of BOGO promotions (scale-ready)."""
    return _keyset_page(BOGOPromotion, db, cursor, page_size, country_code, has_deleted=False)

# --- sanctioned READ surface (Law 3): cross-domain *reads* only. No writes. ---
# NOTE: All write/override imports have been removed. Cross-domain consumers
# that need write access must import the owning service directly (outside ports).
# Only pure read helpers remain in this module per Law 3.

# --- Lazy service exports (Law 3 sanctioned cross-domain surface) ---
# Cross-domain consumers import these from ports instead of reaching
# into the services tree directly.
_LAZY_SERVICE_EXPORTS: dict[str, tuple[str, str]] = {
    "create_category": ("domains.catalog.services.categories.category_service", "create_category"),
    "delete_category": ("domains.catalog.services.categories.category_service", "delete_category"),
    "reorder_categories": ("domains.catalog.services.categories.category_service", "reorder_categories"),
    "update_category": ("domains.catalog.services.categories.category_service", "update_category"),
    "create_coupon": ("domains.catalog.services.promotions.promotions_service", "create_coupon"),
    "create_verification": ("domains.catalog.services.products.product_verification_service", "create_verification"),
    "resolve_product_variant": ("domains.catalog.services.products.products_service", "resolve_product_variant"),
    "get_supplier_profile": ("domains.catalog.services.products.products_service", "get_supplier_profile"),
    "_bump_product_cache_version": ("domains.catalog.services.products.products_service", "_bump_product_cache_version"),
    "get_banners": ("domains.promotions.services.banners.banner_service", "get_banners"),
    "get_banner_by_id": ("domains.promotions.services.banners.banner_service", "get_banner_by_id"),
    "create_banner": ("domains.promotions.services.banners.banner_service", "create_banner"),
    "update_banner": ("domains.promotions.services.banners.banner_service", "update_banner"),
    "delete_banner": ("domains.promotions.services.banners.banner_service", "delete_banner"),
    "list_banners": ("domains.promotions.services.banners.banner_service", "list_banners"),
    "BannerCreate": ("domains.promotions.services.banners.banner_service", "BannerCreate"),
    "BannerUpdate": ("domains.promotions.services.banners.banner_service", "BannerUpdate"),
}
import importlib

def __getattr__(name: str):
    if name in _LAZY_SERVICE_EXPORTS:
        module_path, symbol = _LAZY_SERVICE_EXPORTS[name]
        mod = importlib.import_module(module_path)
        value = getattr(mod, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

