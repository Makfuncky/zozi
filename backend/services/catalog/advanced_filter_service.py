import functools
import hashlib
import json
from typing import Any, Dict, List, Optional

from sqlalchemy import func, and_, or_, case, cast, String
from sqlalchemy.orm import Session

from data.models import Product, Category, ProductVideo, ProductFilterMetadata, ProductFilterOption


class AdvancedFilterService:
    _cache: Dict[str, Dict[str, Any]] = {}
    _cache_ttl = 300
    
    def __init__(self, db: Session):
        self.db = db
        self._cache_version = 0

    def _get_cache_key(self, category_id: Optional[int], search_query: Optional[str], filters: Optional[Dict] = None) -> str:
        key_data = json.dumps({
            "category_id": category_id,
            "search_query": search_query,
            "filters": filters or {},
            "version": self._cache_version
        }, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    def _invalidate_cache(self):
        self._cache_version += 1
        self._cache.clear()

    def get_available_filters(self, category_id: Optional[int] = None, search_query: Optional[str] = None) -> Dict[str, Any]:
        cache_key = self._get_cache_key(category_id, search_query)
        if cache_key in self._cache:
            return self._cache[cache_key]

        base_query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        if category_id is not None:
            base_query = base_query.filter(Product.category_id == category_id)

        if search_query:
            like = f"%{search_query.lower()}%"
            base_query = base_query.filter(
                or_(
                    Product.name.ilike(like),
                    Product.description.ilike(like),
                    Product.category.ilike(like),
                    Product.brand.ilike(like),
                    cast(Product.tags, String).ilike(like),
                )
            )

        price_stats = self._get_price_stats(base_query)
        brands = self._get_brands(base_query)
        ratings = self._get_ratings(base_query)
        attributes = self._get_filter_metadata(category_id, base_query)
        video_count = self._get_video_count(base_query)
        discount_count = self._get_discount_count(base_query)

        result = {
            "price_range": price_stats,
            "brands": brands,
            "ratings": ratings,
            "attributes": attributes,
            "video_count": video_count,
            "discount": discount_count,
        }
        
        self._cache[cache_key] = result
        return result

    def get_active_filters_summary(self, category_id: Optional[int] = None, search_query: Optional[str] = None) -> Dict[str, Any]:
        base_query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        if category_id is not None:
            base_query = base_query.filter(Product.category_id == category_id)

        if search_query:
            like = f"%{search_query.lower()}%"
            base_query = base_query.filter(
                or_(
                    Product.name.ilike(like),
                    Product.description.ilike(like),
                    Product.category.ilike(like),
                    Product.brand.ilike(like),
                    cast(Product.tags, String).ilike(like),
                )
            )

        return {
            "total_products": base_query.count(),
            "has_video": base_query.filter(Product.video_count > 0).count(),
            "has_discount": base_query.filter(
                Product.compare_price.isnot(None),
                Product.compare_price > Product.price,
            ).count(),
            "in_stock": base_query.filter(Product.stock > 0).count(),
        }

    def apply_filters(self, query, filters: Dict[str, Any]):
        if filters.get("min_price") is not None:
            try:
                query = query.filter(Product.price >= float(filters["min_price"]))
            except (TypeError, ValueError):
                pass
        if filters.get("max_price") is not None:
            try:
                query = query.filter(Product.price <= float(filters["max_price"]))
            except (TypeError, ValueError):
                pass

        brands = filters.get("brands")
        if brands:
            if isinstance(brands, list):
                query = query.filter(Product.brand.in_(brands))

        if filters.get("min_rating") is not None:
            try:
                query = query.filter(Product.rating >= float(filters["min_rating"]))
            except (TypeError, ValueError):
                pass

        if filters.get("max_rating") is not None:
            try:
                query = query.filter(Product.rating <= float(filters["max_rating"]))
            except (TypeError, ValueError):
                pass

        attributes = filters.get("attributes")
        if isinstance(attributes, dict):
            for attr_key, attr_values in attributes.items():
                if not attr_values:
                    continue
                if isinstance(attr_values, list) and attr_values:
                    query = query.filter(
                        and_(
                            Product.filter_attributes.has_key(attr_key),
                            cast(Product.filter_attributes[attr_key], String).in_([str(v) for v in attr_values]),
                        )
                    )

        if filters.get("has_video") is True:
            query = query.filter(Product.video_count > 0)

        if filters.get("has_discount") is True:
            query = query.filter(
                Product.compare_price.isnot(None),
                Product.compare_price > Product.price,
            )

        if filters.get("in_stock") is True:
            query = query.filter(Product.stock > 0)

        if filters.get("new_arrivals") is True:
            from datetime import datetime, timedelta, timezone
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60)
            query = query.filter(Product.created_at >= cutoff)

        if filters.get("best_sellers") is True:
            query = query.filter(Product.sales_count >= 5)

        if filters.get("trending") is True:
            query = query.filter(Product.sales_count >= 1).order_by(Product.sales_count.desc())

        return query

    def get_filtered_products(self, filters: Dict[str, Any], limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        cache_key = self._get_cache_key(None, None, filters)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, dict) and "products" in cached:
                return cached

        query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        query = self.apply_filters(query, filters)
        
        total = query.count()
        products = query.offset(offset).limit(limit).all()

        result = {
            "products": [self._serialize_product(p) for p in products],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
        
        self._cache[cache_key] = result
        return result

    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0,
            "rating": float(product.rating) if product.rating else 0,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "stock": product.stock,
            "video_count": product.video_count or 0,
        }

    def build_search_vector(self, product: Product) -> Dict[str, Any]:
        return {
            "name": product.name,
            "description": product.description,
            "category": product.category,
            "brand": product.brand,
            "tags": product.tags,
            "ai_description": product.ai_description,
            "materials": product.materials,
            "color": product.color,
            "sizes": getattr(product, "sizes", None),
        }

    def _get_price_stats(self, base_query) -> Dict[str, float]:
        result = base_query.with_entities(
            func.min(Product.price).label("min_price"),
            func.max(Product.price).label("max_price"),
            func.avg(Product.price).label("avg_price"),
        ).first()

        return {
            "min": float(result.min_price) if result.min_price is not None else 0,
            "max": float(result.max_price) if result.max_price is not None else 0,
            "avg": float(result.avg_price) if result.avg_price is not None else 0,
        }

    def _get_brands(self, base_query) -> List[Dict[str, Any]]:
        rows = (
            base_query.with_entities(
                Product.brand,
                func.count(Product.id).label("count"),
            )
            .filter(Product.brand.isnot(None), Product.brand != "")
            .group_by(Product.brand)
            .order_by(func.count(Product.id).desc())
            .limit(50)
            .all()
        )

        return [{"brand": row.brand, "count": int(row.count)} for row in rows]

    def _get_ratings(self, base_query) -> List[Dict[str, Any]]:
        distribution: Dict[str, int] = {}
        for rating_low, rating_high, label in [
            (4.0, 5.0, "4_stars"),
            (3.0, 4.0, "3_stars"),
            (2.0, 3.0, "2_stars"),
            (1.0, 2.0, "1_star"),
        ]:
            count = base_query.filter(Product.rating >= rating_low, Product.rating < rating_high).count()
            distribution[label] = count

        return [
            {"min_rating": 4, "label": "4★ & up", "count": distribution.get("4_stars", 0)},
            {"min_rating": 3, "label": "3★ & up", "count": distribution.get("3_stars", 0)},
            {"min_rating": 2, "label": "2★ & up", "count": distribution.get("2_stars", 0)},
            {"min_rating": 1, "label": "1★ & up", "count": distribution.get("1_star", 0)},
        ]

    def _get_filter_metadata(self, category_id: Optional[int], base_query) -> List[Dict[str, Any]]:
        metadata_query = self.db.query(ProductFilterMetadata)
        if category_id is not None:
            metadata_query = metadata_query.filter(ProductFilterMetadata.category_id == category_id)
        else:
            metadata_query = metadata_query.filter(ProductFilterMetadata.category_id.is_(None))

        metadata = metadata_query.filter(ProductFilterMetadata.is_active == True).all()

        filters: List[Dict[str, Any]] = []
        for meta in metadata:
            options = (
                self.db.query(ProductFilterOption)
                .filter(ProductFilterOption.filter_metadata_id == meta.id)
                .order_by(ProductFilterOption.sort_order)
                .all()
            )
            filters.append(
                {
                    "id": meta.id,
                    "name": meta.filter_name,
                    "type": meta.filter_type,
                    "display_order": meta.display_order,
                    "options": [
                        {
                            "value": opt.option_value,
                            "display": opt.option_display_name,
                            "count": opt.product_count,
                        }
                        for opt in options
                    ],
                }
            )

        return filters

    def _get_video_count(self, base_query) -> Dict[str, int]:
        return {"with_video": base_query.filter(Product.video_count > 0).count()}

    def _get_discount_count(self, base_query) -> Dict[str, Any]:
        discount_products = base_query.filter(
            Product.compare_price.isnot(None),
            Product.compare_price > Product.price,
        ).count()
        return {"with_discount": discount_products}

