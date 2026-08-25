"""Recommendation Service — personalized product recommendations for customers.

Provides:
- "May you like" — personalized recommendations based on purchase history, wishlist, and browsing
- "Last seen" — recently viewed products
- Personalized product feeds

Wired to providers/ai/ for ML-based recommendations when available.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product, WishlistItem
from domains.orders.models.orders import Order, OrderItem
from infrastructure.utils.cache import cache_or_compute

logger = logging.getLogger(__name__)


def get_last_seen(
    db: Session,
    user_id: int,
    limit: int = 12,
    recent_product_ids: Optional[list[int]] = None,
) -> dict:
    """Return recently viewed products for a user.

    If recent_product_ids is provided (from frontend browsing history),
    returns those products. Otherwise falls back to recently purchased items.
    """
    if recent_product_ids:
        products = (
            db.query(Product)
            .filter(
                Product.id.in_(recent_product_ids),
                Product.is_deleted.is_(False),
                Product.is_active.is_(True),
                Product.stock > 0,
            )
            .all()
        )
        # Preserve order from recent_product_ids
        product_map = {p.id: p for p in products}
        ordered = [product_map[pid] for pid in recent_product_ids if pid in product_map]
        return {
            "source": "browsing_history",
            "products": [_serialize_product(p) for p in ordered[:limit]],
            "results": [_serialize_product(p) for p in ordered[:limit]],
        }

    # Fallback: recently purchased products
    purchased = (
        db.query(Product)
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
        )
        .order_by(desc(Order.created_at))
        .distinct()
        .limit(limit)
        .all()
    )
    return {
        "source": "purchase_history",
        "products": [_serialize_product(p) for p in purchased],
        "results": [_serialize_product(p) for p in purchased],
    }


def get_may_you_like(
    db: Session,
    user_id: Optional[int],
    limit: int = 8,
    recent_categories: Optional[list[str]] = None,
) -> dict:
    """Personalized "may you like" recommendations.

    Algorithm:
    1. Build category preference from purchased quantities
    2. Blend wishlist product categories (lower weight)
    3. Blend recent browsing categories from frontend
    4. Price-preference soft sort
    5. Item-item collaborative signal ("also bought")
    6. Recommend in-stock active products from top categories
    """
    normalized_recent_categories = [
        cat.strip() for cat in (recent_categories or []) if cat and cat.strip()
    ]

    if user_id is None:
        return _get_guest_recommendations(db, limit, normalized_recent_categories)

    _cats_key = ",".join(sorted(normalized_recent_categories))
    _cache_key = f"rec:maylike:{user_id}:{limit}:{hash(_cats_key)}"

    def _compute_payload() -> dict:
        return _compute_may_you_like(db, user_id, limit, normalized_recent_categories)

    return cache_or_compute(
        key=_cache_key,
        compute=_compute_payload,
        ttl=300,
        namespace="customers:recommendations",
    )


def _get_guest_recommendations(
    db: Session,
    limit: int,
    recent_categories: list[str],
) -> dict:
    """Recommendations for unauthenticated users — based on browsing categories only."""
    query = db.query(Product).filter(
        Product.is_deleted.is_(False),
        Product.is_active.is_(True),
        Product.is_approved.is_(True),
        Product.stock > 0,
    )
    if recent_categories:
        query = query.filter(Product.category.in_(recent_categories))

    recommended = query.order_by(Product.sales_count.desc(), Product.rating.desc()).limit(limit).all()
    if not recommended and recent_categories:
        recommended = (
            db.query(Product)
            .filter(
                Product.is_deleted.is_(False),
                Product.is_active.is_(True),
                Product.is_approved.is_(True),
                Product.stock > 0,
            )
            .order_by(Product.sales_count.desc(), Product.rating.desc())
            .limit(limit)
            .all()
        )

    results = [_serialize_product(p) for p in recommended]
    return {
        "source_categories": recent_categories[:4],
        "products": results,
        "results": results,
    }


def _compute_may_you_like(
    db: Session,
    user_id: int,
    limit: int,
    normalized_recent_categories: list[str],
) -> dict:
    """Core recommendation algorithm for authenticated users."""
    # 1. Category preference from purchase history
    category_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
            Product.is_approved.is_(True),
        )
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .all()
    )
    weighted_categories: dict[str, float] = {
        (row.category or "Uncategorized"): float(row.units or 0)
        for row in category_rows
    }

    # 2. Wishlist signal
    wishlist_rows = (
        db.query(Product.category)
        .join(WishlistItem, WishlistItem.product_id == Product.id)
        .filter(
            WishlistItem.user_id == user_id,
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
        )
        .all()
    )
    for row in wishlist_rows:
        cat = (row.category or "Uncategorized").strip()
        if cat:
            weighted_categories[cat] = weighted_categories.get(cat, 0) + 0.3

    # 3. Recent browsing signal
    for category in normalized_recent_categories:
        clean = (category or "").strip()
        if clean:
            weighted_categories[clean] = weighted_categories.get(clean, 0) + 0.5

    # 4. Collaborative signal ("also bought")
    user_product_ids_subq = (
        db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .limit(20)
        .scalar_subquery()
    )
    co_order_ids_subq = (
        db.query(OrderItem.order_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            OrderItem.product_id.in_(user_product_ids_subq),
            Order.user_id != user_id,
        )
        .distinct()
        .limit(100)
        .scalar_subquery()
    )
    also_bought_rows = (
        db.query(Product.category, func.count(OrderItem.product_id).label("co_count"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .filter(
            OrderItem.order_id.in_(co_order_ids_subq),
            Product.id.notin_(user_product_ids_subq),
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
            Product.is_approved.is_(True),
        )
        .group_by(Product.category)
        .limit(50)
        .all()
    )
    for row in also_bought_rows:
        cat = (row.category or "Uncategorized").strip()
        if cat:
            boost = min(float(row.co_count) * 0.2, 3.0)
            weighted_categories[cat] = weighted_categories.get(cat, 0) + boost

    # 5. Price-preference signal
    price_avg_row = (
        db.query(func.avg(Product.price).label("avg_price"))
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .first()
    )
    price_band_lo: Optional[float] = None
    price_band_hi: Optional[float] = None
    if price_avg_row and price_avg_row.avg_price:
        avg = float(price_avg_row.avg_price)
        price_band_lo = avg * 0.4
        price_band_hi = avg * 2.5

    # 6. Build recommendation query
    top_categories = [
        cat for cat, _score in sorted(
            weighted_categories.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )[:4]
    ]

    purchased_product_ids = {
        row.product_id
        for row in db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    }

    query = db.query(Product).filter(
        Product.is_deleted.is_(False),
        Product.is_active.is_(True),
        Product.is_approved.is_(True),
        Product.stock > 0,
    )
    if purchased_product_ids:
        query = query.filter(Product.id.notin_(purchased_product_ids))
    if top_categories:
        query = query.filter(Product.category.in_(top_categories))

    recommended = query.order_by(Product.sales_count.desc(), Product.rating.desc()).limit(limit).all()
    if not recommended:
        fallback_query = db.query(Product).filter(
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
            Product.is_approved.is_(True),
            Product.stock > 0,
        )
        if purchased_product_ids:
            fallback_query = fallback_query.filter(Product.id.notin_(purchased_product_ids))
        recommended = fallback_query.order_by(
            Product.sales_count.desc(), Product.rating.desc(),
        ).limit(limit).all()

    # Apply price-preference soft sort
    if price_band_lo is not None:
        def _out_of_band(p: Product) -> int:
            prc = float(getattr(p, "price", 0) or 0)
            return 0 if price_band_lo <= prc <= price_band_hi else 1
        recommended = sorted(recommended, key=_out_of_band)

    results = [_serialize_product(p) for p in recommended]
    return {
        "source_categories": top_categories,
        "products": results,
        "results": results,
    }


def _serialize_product(product: Product) -> dict[str, Any]:
    """Serialize a Product ORM object to a dict."""
    return {
        "id": product.id,
        "name": product.name,
        "price": float(product.price) if product.price is not None else 0.0,
        "rating": float(product.rating) if product.rating is not None else 0.0,
        "brand": getattr(product, "brand", None),
        "image_url": getattr(product, "image_url", None),
        "category": product.category,
        "stock": product.stock,
    }


__all__ = [
    "get_last_seen",
    "get_may_you_like",
    "get_may_you_like",
]
