"""
Products Controller — all product CRUD and supplier upload business logic.
"""
import html
import hashlib
import json
import os
import uuid
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, List, Optional, cast

from fastapi.encoders import jsonable_encoder
from fastapi import HTTPException, UploadFile
from fastapi.responses import Response
from sqlalchemy import func, or_, text
from sqlalchemy.orm import Session, selectinload

from domains.governance.models.core import CartItem
from domains.governance.models.user import User
from domains.catalog.models.products import Category
from domains.catalog.models.products import Product
from domains.catalog.models.products import ProductVariant
from domains.catalog.models.products import Review
from domains.catalog.models.products import Wishlist
from domains.comms.models.communication import Notification
from domains.comms.models.marketing import FlashSale
from domains.comms.models.suppliers import SupplierProfile
from domains.country.models.countries import CountryConfig
from domains.orders.models.orders import Order
from domains.orders.models.orders import OrderItem
from infrastructure.database.schemas import Product as ProductSchema, ProductCreate
from infrastructure.utils.audit import audit_log, AuditAction
from infrastructure.utils.cache import cache_or_compute, cache_get_json, cache_set_json
from infrastructure.utils.performance_cache import cache_product_listing, set_product_listing, invalidate_product_listings
from infrastructure.utils.pagination import paginated_response
from domains.country.utils.country_rls import get_country_or_404
from infrastructure.utils.rls_interceptor import set_rls_context, clear_rls_context

logger = logging.getLogger(__name__)

from infrastructure.observability.service_observability import (
    db_query_timer,
    get_correlation_id,
    log_service_call,
    log_service_error,
    request_context,
)


_MONEY_QUANT = Decimal("0.01")
_PRODUCT_LIST_CACHE_TTL = 60
_PRODUCT_DETAIL_CACHE_TTL = 120
_PRODUCT_CACHE_VERSION_KEY = "products:cache:version"
_PUBLIC_PRODUCTS_CACHE_CONTROL = "public, max-age=30, stale-while-revalidate=60"

_CATEGORY_LOOKUP_ALIASES: dict[str, str] = {
    "smoke": "general",
    "validation": "general",
    "furniture": "furniture",
    "home and living": "home-living",
    "home & living": "home-living",
}


def _normalize_product_visibility_regions(value: Any) -> str | None:
    if value in (None, "", [], ()): 
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            parsed = json.loads(stripped)
        except (TypeError, ValueError, json.JSONDecodeError):
            parsed = [item.strip() for item in stripped.split(",") if item.strip()]
    elif isinstance(value, list):
        parsed = value
    else:
        parsed = [str(value).strip()]

    normalized: list[str] = []
    seen: set[str] = set()
    for item in parsed:
        candidate = str(item).strip()
        if not candidate:
            continue
        key = candidate.casefold()
        if key in seen:
            continue
        seen.add(key)
        normalized.append(candidate)
    return json.dumps(normalized) if normalized else None


def _prepare_product_write_payload(data: dict[str, Any]) -> dict[str, Any]:
    payload = dict(data)
    if "subcategory" in payload:
        subcategory = str(payload["subcategory"]).strip() if payload["subcategory"] is not None else ""
        payload["subcategory"] = subcategory or None
    if "visibility_regions" in payload:
        payload["visibility_regions"] = _normalize_product_visibility_regions(payload.get("visibility_regions"))
    return payload


def _category_lookup_tokens(value: str) -> list[str]:
    tokens: list[str] = []
    raw = value.strip().casefold()
    if not raw:
        return tokens
    for candidate in (raw, raw.replace("-", " "), raw.replace("&", "and")):
        normalized = candidate.strip()
        if normalized and normalized not in tokens:
            tokens.append(normalized)
    alias = _CATEGORY_LOOKUP_ALIASES.get(raw)
    if alias and alias not in tokens:
        tokens.append(alias)
        if "-" in alias:
            spaced_alias = alias.replace("-", " ")
            if spaced_alias not in tokens:
                tokens.append(spaced_alias)
    return tokens


def _resolve_product_category_fields(payload: dict[str, Any], db: Session) -> dict[str, Any]:
    resolved = dict(payload)
    category_id = resolved.get("category_id")
    category_name = str(resolved.get("category") or "").strip()

    matched_category = None
    if category_id is not None:
        matched_category = db.query(Category).filter(Category.id == category_id).first()
        if matched_category is None:
            raise HTTPException(status_code=422, detail="Selected category was not found")
    elif category_name:
        lookup_tokens = _category_lookup_tokens(category_name)
        matched_category = db.query(Category).filter(
            or_(func.lower(Category.name).in_(lookup_tokens), func.lower(Category.slug).in_(lookup_tokens))
        ).first()

    if matched_category is not None:
        resolved["category_id"] = cast(int, getattr(matched_category, "id"))
        resolved["category"] = cast(str, getattr(matched_category, "name"))
    elif "category_id" in resolved:
        resolved["category_id"] = None

    return resolved


def _get_redis_client():
    try:
        from infrastructure.utils.auth import _get_redis
        return _get_redis()
    except Exception:
        return None


def _cache_get_json(key: str) -> Any | None:
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            return None
        raw = redis_client.get(key)
        if not raw:
            return None
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8")
        return json.loads(cast(str, raw))
    except Exception:
        return None


def _cache_set_json(key: str, value: Any, ttl: int) -> None:
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            return
        redis_client.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def _get_product_cache_version() -> str:
    try:
        redis_client = _get_redis_client()
        if redis_client is None:
            return "0"
        raw = redis_client.get(_PRODUCT_CACHE_VERSION_KEY)
        if raw is None:
            redis_client.set(_PRODUCT_CACHE_VERSION_KEY, "1")
            return "1"
        if isinstance(raw, (bytes, bytearray)):
            return raw.decode("utf-8")
        return str(raw)
    except Exception:
        return "0"


def _bump_product_cache_version() -> None:
    from infrastructure.utils.cache import bump_product_cache_version as _bump

    _bump()


def _build_product_cache_key(prefix: str, payload: dict[str, Any]) -> str:
    version = _get_product_cache_version()
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return f"products:{prefix}:v{version}:{digest}"


def _serialize_product(product: Product) -> dict[str, Any]:
    return cast(dict[str, Any], jsonable_encoder(ProductSchema.model_validate(product)))


def _serialize_products(products: list[Product]) -> list[dict[str, Any]]:
    return [_serialize_product(product) for product in products]


def _normalize_variant_selector(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def resolve_product_variant(product: Product, selected_size: Optional[str], selected_color: Optional[str]) -> Optional[ProductVariant]:
    variants = list(getattr(product, "variants", []) or [])
    if not variants:
        return None

    normalized_size = _normalize_variant_selector(selected_size)
    normalized_color = _normalize_variant_selector(selected_color)
    if not normalized_size and not normalized_color:
        return None

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
        return [str(value).strip().lower() for value in parsed.values() if str(value).strip()]

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


def _normalize_datetime(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(tz=None).replace(tzinfo=None)
    return dt


def _parse_flash_sale_product_ids(raw: Optional[str | list[int]]) -> List[int]:
    if not raw:
        return []
    if isinstance(raw, list):
        product_ids: List[int] = []
        for item in raw:
            try:
                product_ids.append(int(item))
            except (TypeError, ValueError):
                continue
        return product_ids
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    if not isinstance(parsed, list):
        return []
    product_ids: List[int] = []
    for item in parsed:
        try:
            product_ids.append(int(item))
        except (TypeError, ValueError):
            continue
    return product_ids


def _get_active_flash_sales(
    db: Session,
    sale_id: Optional[int] = None,
) -> list[FlashSale]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    query = db.query(FlashSale).filter(
        FlashSale.is_active == True,  # noqa: E712
        FlashSale.starts_at <= now,
        FlashSale.ends_at >= now,
    )
    if sale_id is not None:
        query = query.filter(FlashSale.id == sale_id)
    return query.order_by(FlashSale.discount_pct.desc(), FlashSale.ends_at.asc()).limit(100).all()


def _apply_live_offer_metadata(product: Product, flash_sale: Optional[FlashSale]) -> Product:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    price = cast(Optional[Decimal], getattr(product, "price", None))
    compare_price = cast(Optional[Decimal], getattr(product, "compare_price", None))
    discount_starts_at = _normalize_datetime(cast(Optional[datetime], getattr(product, "discount_starts_at", None)))
    discount_ends_at = _normalize_datetime(cast(Optional[datetime], getattr(product, "discount_ends_at", None)))

    setattr(product, "offer_type", None)
    setattr(product, "offer_title", None)
    setattr(product, "offer_discount_pct", None)
    setattr(product, "offer_starts_at", None)
    setattr(product, "offer_ends_at", None)
    setattr(product, "flash_sale_id", None)

    if flash_sale and price is not None:
        sale_discount = Decimal(str(flash_sale.discount_pct)) / Decimal("100")
        sale_price = (price * (Decimal("1") - sale_discount)).quantize(_MONEY_QUANT, rounding=ROUND_HALF_UP)
        setattr(product, "compare_price", price)
        setattr(product, "price", sale_price)
        setattr(product, "offer_type", "flash_sale")
        setattr(product, "offer_title", flash_sale.title)
        setattr(product, "offer_discount_pct", float(flash_sale.discount_pct))
        setattr(product, "offer_starts_at", flash_sale.starts_at)
        setattr(product, "offer_ends_at", flash_sale.ends_at)
        setattr(product, "flash_sale_id", flash_sale.id)
        return product

    is_supplier_discount_active = (
        compare_price is not None
        and price is not None
        and compare_price > price
        and (discount_starts_at is None or discount_starts_at <= now)
        and (discount_ends_at is None or discount_ends_at >= now)
    )
    if is_supplier_discount_active:
        discount_pct = ((compare_price - price) / compare_price) * Decimal("100")
        setattr(product, "offer_type", "supplier_discount")
        setattr(product, "offer_title", "Supplier Discount")
        setattr(product, "offer_discount_pct", float(discount_pct.quantize(Decimal("1"), rounding=ROUND_HALF_UP)))
        setattr(product, "offer_starts_at", discount_starts_at)
        setattr(product, "offer_ends_at", discount_ends_at)
        return product

    if compare_price is not None and compare_price <= price:
        setattr(product, "compare_price", None)
    elif compare_price is not None and discount_ends_at is not None and discount_ends_at < now:
        setattr(product, "compare_price", None)

    return product


def _is_product_restricted_for_country(
    category_slug: str,
    country_code: str | None,
    db: Session,
) -> bool:
    """Check if a product category is restricted in a given country."""
    if not country_code:
        return False
    from domains.logistics.services.partner.logistics_partner_pricing import normalize_country_code
    import json as _json
    code = normalize_country_code(country_code)
    if not code:
        return False
    country = db.query(CountryConfig).filter(
        CountryConfig.code == code,
        CountryConfig.is_active == True,
    ).first()
    if not country:
        return False
    raw = country.product_restrictions_json
    if not raw:
        return False
    try:
        restricted = _json.loads(raw) if isinstance(raw, str) else raw
    except (_json.JSONDecodeError, TypeError):
        return False
    if not isinstance(restricted, list):
        return False
    slug = category_slug.strip().lower()
    return any(str(r).strip().lower() == slug for r in restricted)


def _list_products_cached(
    db: Session,
    resolved_country: Optional[str],
    q: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    brands: Optional[str] = None,
    color: Optional[str] = None,
    region: Optional[str] = None,
    supplier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    new_arrivals: bool = False,
    best_sellers: bool = False,
    trending: bool = False,
    in_stock: bool = False,
    min_discount: Optional[int] = None,
    deals: bool = False,
    sort: Optional[str] = None,
    sale_id: Optional[int] = None,
    limit: int = 24,
    offset: int = 0,
    country_code: Optional[str] = None,
    has_video: bool = False,
    attributes: Optional[str] = None,
) -> tuple[list[dict[str, Any]], int]:
    query = db.query(Product).options(
        selectinload(Product.variants),
    ).filter(
        Product.is_deleted == False,           # noqa: E712
        Product.is_active.isnot(False),        # NULL → active
        Product.is_approved.isnot(False),      # NULL → approved
    )

    active_sales = _get_active_flash_sales(db, sale_id=sale_id)
    active_sales_by_product: dict[int, FlashSale] = {}
    global_flash_sale: Optional[FlashSale] = None
    sale_product_ids: set[int] = set()
    for sale in active_sales:
        scoped_product_ids = _parse_flash_sale_product_ids(sale.product_ids)
        if not scoped_product_ids:
            global_flash_sale = global_flash_sale or sale
            continue
        for product_id in scoped_product_ids:
            sale_product_ids.add(product_id)
            active_sales_by_product.setdefault(product_id, sale)

    if sale_id is not None:
        if not sale_product_ids and global_flash_sale is None:
            return [], 0
        if global_flash_sale is None:
            query = query.filter(Product.id.in_(sale_product_ids))

    if category and category.lower() != "all":
        query = query.filter(Product.category.ilike(category))
    if subcategory:
        query = query.filter(Product.subcategory.ilike(subcategory))
    if brand:
        query = query.filter(Product.brand.ilike(f"%{brand}%"))
    if brands:
        brand_list = [b.strip() for b in brands.split(",") if b.strip()]
        if brand_list:
            query = query.filter(Product.brand.in_(brand_list))
    if color:
        query = query.filter(Product.color.ilike(f"%{color}%"))
    if region:
        normalized_region = region.strip().lower()
        if normalized_region:
            region_pattern = f'%"{normalized_region}"%'
            query = query.filter(
                or_(
                    Product.visibility_regions.is_(None),
                    Product.visibility_regions == "[]",
                    func.lower(Product.visibility_regions).like(region_pattern),
                )
            )

    if supplier:
        names = [s.strip() for s in supplier.split(",") if s.strip()]
        if names:
            query = query.join(User, Product.supplier_id == User.id).outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
            if len(names) == 1:
                term = f"%{names[0]}%"
                query = query.filter(
                    or_(
                        User.username.ilike(term),
                        SupplierProfile.business_name.ilike(term),
                    )
                )
            else:
                query = query.filter(
                    or_(
                        User.username.in_(names),
                        SupplierProfile.business_name.in_(names),
                    )
                )

    if q:
        term = f"%{q.lower()}%"
        query = query.filter(
            Product.name.ilike(term)
            | Product.description.ilike(term)
            | Product.category.ilike(term)
            | Product.subcategory.ilike(term)
        )
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if min_rating is not None:
        query = query.filter(Product.rating >= min_rating)
    if max_rating is not None:
        query = query.filter(Product.rating <= max_rating)

    if new_arrivals:
        cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60)
        query = query.filter(Product.created_at >= cutoff)

    if best_sellers:
        query = query.filter(Product.sales_count >= 5)

    if trending:
        query = query.filter(Product.sales_count >= 1).order_by(Product.sales_count.desc())

    if in_stock:
        query = query.filter(Product.stock > 0)

    if has_video:
        query = query.filter(Product.video_count > 0)

    if min_discount is not None and min_discount > 0:
        # Skip this DB-level filter when a global flash sale is active AND deals mode is on:
        # the in-memory pricing pass will apply the flash sale to every returned product,
        # so restricting by stored compare_price would wrongly exclude flash-sale-only items.
        _skip_discount_filter = deals and global_flash_sale is not None
        if not _skip_discount_filter:
            factor = 1.0 - min_discount / 100.0
            query = query.filter(
                Product.compare_price.isnot(None),
                Product.compare_price > Product.price,
                Product.price <= Product.compare_price * factor,
                or_(Product.discount_starts_at.is_(None), Product.discount_starts_at <= datetime.now(timezone.utc).replace(tzinfo=None)),
                or_(Product.discount_ends_at.is_(None), Product.discount_ends_at >= datetime.now(timezone.utc).replace(tzinfo=None)),
            )

    if sort == "price_asc":
        query = query.order_by(Product.price.asc())
    elif sort == "price_desc":
        query = query.order_by(Product.price.desc())
    elif sort == "name_asc":
        query = query.order_by(Product.name.asc())
    elif sort == "newest":
        query = query.order_by(Product.created_at.desc())
    elif sort == "rating":
        query = query.order_by(Product.rating.desc())
    elif sort == "bestseller":
        query = query.order_by(Product.sales_count.desc())
    elif sort == "discount":
        query = query.order_by(
            Product.compare_price.desc().nullslast(),
            Product.price.asc(),
        )

    products = query.offset(offset).limit(limit).all()
    total = query.count()
    hydrated_products = [
        _apply_live_offer_metadata(product, active_sales_by_product.get(product.id) or global_flash_sale)
        for product in products
    ]
    serialized_products = _serialize_products(hydrated_products)

    if resolved_country:
        from domains.logistics.services.partner.logistics_partner_pricing import normalize_country_code
        code = normalize_country_code(resolved_country)
        restriction_cache: dict[str, bool] = {}
        if code:
            from domains.country.models.countries import CountryConfig
            country = db.query(CountryConfig).filter(
                CountryConfig.code == code,
                CountryConfig.is_active == True,
            ).first()
            if country and country.product_restrictions_json:
                try:
                    raw = country.product_restrictions_json
                    restricted_list = json.loads(raw) if isinstance(raw, str) else raw
                    if isinstance(restricted_list, list):
                        restriction_cache = {str(r).strip().lower(): True for r in restricted_list if r}
                except Exception:
                    pass

        def _is_restricted(category_slug: str) -> bool:
            return restriction_cache.get((category_slug or "").strip().lower(), False)

        filtered_products = [prod for prod in serialized_products if not _is_restricted(prod.get("category", ""))]
        serialized_products = filtered_products

    return serialized_products, total


def get_products(
    db: Session,
    response: Optional[Response],
    q: Optional[str] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    brand: Optional[str] = None,
    brands: Optional[str] = None,
    color: Optional[str] = None,
    region: Optional[str] = None,
    supplier: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    max_rating: Optional[float] = None,
    new_arrivals: bool = False,
    best_sellers: bool = False,
    trending: bool = False,
    in_stock: bool = False,
    min_discount: Optional[int] = None,
    deals: bool = False,
    sort: Optional[str] = None,
    sale_id: Optional[int] = None,
    limit: int = 24,
    offset: int = 0,
    country_code: Optional[str] = None,
    has_video: bool = False,
    attributes: Optional[str] = None,
) -> List[Product]:
    resolved_country = country_code or region

    cache_payload = {
        "q": q,
        "category": category,
        "subcategory": subcategory,
        "brand": brand,
        "brands": brands,
        "color": color,
        "region": region,
        "supplier": supplier,
        "min_price": min_price,
        "max_price": max_price,
        "min_rating": min_rating,
        "max_rating": max_rating,
        "new_arrivals": new_arrivals,
        "best_sellers": best_sellers,
        "trending": trending,
        "in_stock": in_stock,
        "min_discount": min_discount,
        "deals": deals,
        "sort": sort,
        "sale_id": sale_id,
        "limit": limit,
        "offset": offset,
        "country_code": country_code,
        "has_video": has_video,
        "attributes": attributes,
    }
    cache_key = build_versioned_cache_key("products:listing", "list", cache_payload)

    def _compute() -> tuple[list[dict[str, Any]], int]:
        return _list_products_cached(
            db=db,
            resolved_country=resolved_country,
            q=q,
            category=category,
            subcategory=subcategory,
            brand=brand,
            brands=brands,
            color=color,
            region=region,
            supplier=supplier,
            min_price=min_price,
            max_price=max_price,
            min_rating=min_rating,
            max_rating=max_rating,
            new_arrivals=new_arrivals,
            best_sellers=best_sellers,
            trending=trending,
            in_stock=in_stock,
            min_discount=min_discount,
            deals=deals,
            sort=sort,
            sale_id=sale_id,
            limit=limit,
            offset=offset,
            country_code=country_code,
            has_video=has_video,
            attributes=attributes,
        )

    serialized_products, total = cache_or_compute(
        key=cache_key,
        compute=_compute,
        ttl=300,
        namespace="products:listing",
    )

    if response is not None:
        response.headers["X-Total-Count"] = str(total)
        response.headers["Cache-Control"] = _PUBLIC_PRODUCTS_CACHE_CONTROL

    return cast(List[Product], serialized_products)


def create_product(product: ProductCreate, db: Session) -> Product:
    try:
        with db_query_timer("insert_product"):
            data = _prepare_product_write_payload(product.model_dump())
            data = _resolve_product_category_fields(data, db)
            data["name"] = html.escape(data["name"].strip()) if data.get("name") else data.get("name")
            if data.get("description"):
                data["description"] = html.escape(data["description"])
            db_product = Product(**data)
            db.add(db_product)
            db.commit()
        _bump_product_cache_version()
        invalidate_product_listings()
        db.refresh(db_product)
        log_service_call("products_service", "create_product", level="info", product_id=db_product.id)
        return db_product
    except Exception as exc:
        log_service_error("products_service", "create_product", exc)
        db.rollback()
        raise


def get_product(product_id: int, db: Session) -> Product:
    cache_key = _build_product_cache_key("detail", {"product_id": product_id})
    cached_payload = _cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    try:
        with db_query_timer("select_product_detail"):
            product = db.query(Product).options(selectinload(Product.variants)).filter(
                Product.id == product_id,
                Product.is_deleted == False,  # noqa: E712
            ).first()
    except Exception as exc:
        log_service_error("products_service", "get_product", exc, product_id=product_id)
        raise
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    active_sales = _get_active_flash_sales(db)
    active_sale = next((sale for sale in active_sales if product_id in _parse_flash_sale_product_ids(sale.product_ids)), None)
    global_sale = next((sale for sale in active_sales if not _parse_flash_sale_product_ids(sale.product_ids)), None)
    hydrated_product = _apply_live_offer_metadata(product, active_sale or global_sale)
    serialized_product = _serialize_product(hydrated_product)
    _cache_set_json(cache_key, serialized_product, _PRODUCT_DETAIL_CACHE_TTL)
    return serialized_product


def update_product(product_id: int, product: ProductCreate, current_user: dict, db: Session) -> Product:
    db_product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
    ).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")
    data = _prepare_product_write_payload(product.model_dump())
    data = _resolve_product_category_fields(data, db)
    if data.get("name"):
        data["name"] = html.escape(data["name"].strip())
    if data.get("description"):
        data["description"] = html.escape(data["description"])
    for key, value in data.items():
        setattr(db_product, key, value)
    db.commit()
    _bump_product_cache_version()
    db.refresh(db_product)
    audit_log(
        db,
        action=AuditAction.PRODUCT_UPDATE,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"name": db_product.name},
    )
    return db_product


def delete_product(product_id: int, current_user: dict, db: Session) -> dict:
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    product_name = str(product.name)

    # Cascade: remove from carts and wishlists
    db.query(CartItem).filter(CartItem.product_id == product_id).delete(synchronize_session=False)
    db.query(Wishlist).filter(Wishlist.product_id == product_id).delete(synchronize_session=False)

    # Cascade: soft-delete reviews
    db.query(Review).filter(
        Review.product_id == product_id,
        Review.is_deleted == False,  # noqa: E712
    ).update({"is_deleted": True}, synchronize_session=False)

    # Cascade: notify users with in-flight orders
    affected_orders = (
        db.query(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(
            OrderItem.product_id == product_id,
            Order.status.in_(["pending", "processing", "confirmed"]),
        )
        .all()
    )
    for order in affected_orders:
        db.add(Notification(
            user_id=order.user_id,
            type="system",
            title="Product Unavailable",
            message=(
                f"A product ('{product_name}') in your order #{order.id} "
                "is no longer available. Our support team will contact you."
            ),
            link=f"/orders/{order.id}",
        ))

    setattr(product, "is_deleted", True)
    db.commit()
    _bump_product_cache_version()
    audit_log(
        db,
        action=AuditAction.PRODUCT_DELETE,
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=current_user.get("role"),
        resource_type="product",
        resource_id=product_id,
        details={"product_name": product_name, "orders_notified": len(affected_orders)},
    )
    return {"message": "Product deleted", "orders_notified": len(affected_orders)}


def update_product_return_window(
    product_id: int,
    days: int,
    current_user: dict,
    db: Session,
) -> dict:
    """
    Supplier sets the return window (days) for a specific product.

    Constraints:
      - Minimum: 10 days (platform minimum)
      - Maximum: supplier's max_return_days (default 30) from SupplierProfile
    """
    if days < 10:
        raise HTTPException(status_code=422, detail="Return window must be at least 10 days")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    # Check against supplier's configured maximum
    supplier_profile = db.query(SupplierProfile).filter(
        SupplierProfile.user_id == current_user["id"]
    ).first()
    max_days = int(supplier_profile.max_return_days) if supplier_profile and supplier_profile.max_return_days else 30
    if days > max_days:
        raise HTTPException(
            status_code=422,
            detail=f"Return window cannot exceed your configured maximum of {max_days} days",
        )

    setattr(product, "return_window_days", days)
    db.commit()
    return {"message": "Return window updated", "return_window_days": days}


_LOW_STOCK_THRESHOLD = 5


def patch_product_stock(
    product_id: int,
    delta: int,
    current_user: dict,
    db: Session,
) -> dict:
    """Adjust product stock by delta (+/-). Suppliers own their products; admins can adjust any."""
    role = current_user.get("role")

    q = db.query(Product).filter(
        Product.id == product_id,
        Product.is_deleted == False,  # noqa: E712
    )
    if role not in ("admin", "sub_admin"):
        q = q.filter(Product.supplier_id == current_user["id"])

    product = q.first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found or not authorized")

    current_stock = int(cast(Any, getattr(product, "stock")) or 0)
    new_stock = current_stock + delta
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below 0")

    setattr(product, "stock", new_stock)
    db.commit()
    _bump_product_cache_version()

    audit_log(
        db,
        action=getattr(AuditAction, "PRODUCT_STOCK_UPDATED", AuditAction.PRODUCT_UPDATE),
        user_id=current_user.get("id"),
        username=current_user.get("username"),
        user_role=role,
        resource_type="product",
        resource_id=product_id,
        details={"delta": delta, "new_stock": new_stock},
    )

    # Low-stock email alert to supplier (non-blocking)
    supplier_id = cast(int | None, getattr(product, "supplier_id"))
    if new_stock <= _LOW_STOCK_THRESHOLD and supplier_id:
        try:
            from domains.governance.ports import User as UserModel
            from infrastructure.utils.email_service import send_email
            supplier = db.query(UserModel).filter(UserModel.id == supplier_id).first()
            supplier_email = cast(str | None, getattr(supplier, "email")) if supplier else None
            if supplier and supplier_email:
                html_body = f"""
                <h2 style="font-family:Arial,sans-serif;color:#dc2626">Low Stock Alert</h2>
                <p style="font-family:Arial,sans-serif;color:#374151">
                  Product <strong>{product.name}</strong> (ID: {product.id}) 
                  has only <strong>{new_stock}</strong> unit(s) remaining.
                </p>
                <p style="font-family:Arial,sans-serif;color:#6b7280">
                  Please restock soon to avoid losing sales.
                </p>"""
                send_email(
                    to=supplier_email,
                    subject=f"ZOZI Low Stock Alert: {product.name}",
                    html=html_body,
                )
        except Exception as exc:
            logger.warning("Low-stock email failed (non-fatal): %s", exc)

    return {"product_id": product_id, "new_stock": new_stock, "delta": delta}


def atomic_stock_decrement(db: Session, product_id: int, quantity: int) -> bool:
    """Atomically decrement product stock if sufficient quantity exists.

    Uses a single ``UPDATE ... WHERE stock >= quantity`` statement to prevent
    oversell under concurrent requests. The database's row-level locking ensures
    that concurrent decrements are serialized — only transactions where stock is
    sufficient will succeed.

    Args:
        db: Database session.
        product_id: Product whose stock to decrement.
        quantity: Number of units to remove from stock.

    Returns:
        True if the stock was successfully decremented.

    Raises:
        HTTPException: 409 if insufficient stock (oversell prevented).
        HTTPException: 404 if product not found.
    """
    if quantity <= 0:
        return True

    result = db.execute(
        text(
            "UPDATE commerce.products SET stock = stock - :qty, updated_at = NOW() "
            "WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"
        ),
        {"pid": product_id, "qty": quantity},
    )

    if result.rowcount == 0:
        product = db.query(Product).filter(Product.id == product_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        available = int(getattr(product, "stock", 0) or 0)
        raise HTTPException(
            status_code=409,
            detail=f"Insufficient stock for product {product_id}. Available: {available}, Requested: {quantity}",
        )

    return True


def finalize_inventory_atomic(db: Session, order_id: int) -> list[str]:
    """Atomically finalize inventory for a paid order with oversell prevention.

    Iterates over order items and uses atomic ``UPDATE ... WHERE stock >= quantity``
    for each product. If any item has insufficient stock, collects the issues
    and returns them without modifying any rows.

    Args:
        db: Database session.
        order_id: Order whose inventory to finalize.

    Returns:
        List of issue strings (empty if all items were decremented successfully).
    """
    order_items = (
        db.query(OrderItem)
        .filter(OrderItem.order_id == order_id)
        .all()
    )

    if not order_items:
        return []

    requested_quantities: dict[int, int] = {}
    for item in order_items:
        product_id = int(getattr(item, "product_id"))
        quantity = int(getattr(item, "quantity"))
        requested_quantities[product_id] = requested_quantities.get(product_id, 0) + quantity

    issues: list[str] = []

    for product_id, requested_quantity in requested_quantities.items():
        result = db.execute(
            text(
                "UPDATE commerce.products SET stock = stock - :qty, updated_at = NOW() "
                "WHERE id = :pid AND is_deleted = FALSE AND stock >= :qty"
            ),
            {"pid": product_id, "qty": requested_quantity},
        )

        if result.rowcount == 0:
            product = db.query(Product).filter(Product.id == product_id).first()
            if product is None:
                issues.append(f"missing_product:{product_id}")
            else:
                available = int(getattr(product, "stock", 0) or 0)
                issues.append(
                    f"insufficient_stock:{product.id}:available={available}:requested={requested_quantity}"
                )

    if not issues:
        _bump_product_cache_version()

    return issues


def get_supplier_products_simple(current_user: dict, db: Session) -> List[Product]:
    return db.query(Product).filter(
        Product.supplier_id == current_user["id"],
        Product.is_deleted == False,  # noqa: E712
    ).all()


def create_supplier_product_with_upload(
    name: str,
    description: str,
    price: float,
    category: str,
    color: str,
    stock: int,
    file: UploadFile,
    current_user: dict,
    db: Session,
) -> Product:
    from infrastructure.utils.file_validation import validate_upload_image
    from infrastructure.utils.storage import storage as _storage

    MAX_SIZE = 10 * 1024 * 1024  # 10 MB
    content = file.file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="Image file exceeds 10MB limit")

    validated_ext = validate_upload_image(content, file.filename or "upload")
    safe_filename = f"{uuid.uuid4().hex}{validated_ext}"
    key = f"products/{safe_filename}"
    url = _storage.save(key, content, content_type=file.content_type)

    product = Product(
        name=html.escape(name.strip()) if name else name,
        description=html.escape(description) if description else description,
        price=price,
        category=category,
        color=color,
        image_url=url,
        stock=stock,
        supplier_id=current_user["id"],
    )
    category_match = db.query(Category).filter(
        or_(func.lower(Category.name) == category.strip().casefold(), func.lower(Category.slug) == category.strip().casefold())
    ).first() if category and category.strip() else None
    if category_match is not None:
        product.category_id = cast(int, getattr(category_match, "id"))
        product.category = cast(str, getattr(category_match, "name"))
    db.add(product)
    db.commit()
    _bump_product_cache_version()
    db.refresh(product)
    return product


def autocomplete_products(q: str, db: Session) -> List[str]:
    term = f"%{q.lower()}%"
    results = db.query(Product.name).filter(Product.name.ilike(term)).limit(10).all()
    return [r[0] for r in results]


def get_supplier_names(db: Session) -> List[str]:
    """Return supplier usernames and storefront business names for filtering."""
    results = (
        db.query(User.username, SupplierProfile.business_name)
        .join(Product, Product.supplier_id == User.id)
        .outerjoin(SupplierProfile, SupplierProfile.user_id == User.id)
        .filter(
            User.role == "supplier",
            Product.is_deleted == False,  # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
        )
        .order_by(User.username)
        .all()
    )
    names: list[str] = []
    seen: set[str] = set()
    for username, business_name in results:
        for candidate in (business_name, username):
            if not candidate:
                continue
            normalized = candidate.strip()
            key = normalized.lower()
            if not normalized or key in seen:
                continue
            seen.add(key)
            names.append(normalized)
    return names


def get_product_by_barcode(code: str, db: Session) -> Product:
    """
    Barcode / QR lookup compatibility layer.

    Supported payload shapes:
    - "123"          -> product id
    - "P-123"        -> product id
    - "PROD-123"     -> product id
    - "PRODUCT-123"  -> product id
    """
    raw = (code or "").strip()
    if not raw:
        raise HTTPException(status_code=422, detail="Barcode is required")

    upper = raw.upper()
    candidates = [upper]
    for prefix in ("P-", "PROD-", "PRODUCT-"):
        if upper.startswith(prefix):
            candidates.append(upper[len(prefix):])

    product_id = None
    for candidate in candidates:
        if candidate.isdigit():
            product_id = int(candidate)
            break

    product = None
    if product_id is not None:
        product = db.query(Product).options(selectinload(Product.variants)).filter(
            Product.id == product_id,
            Product.is_deleted == False,   # noqa: E712
            Product.is_active == True,     # noqa: E712
            Product.is_approved == True,   # noqa: E712
        ).first()
    if not product:
        matched_variant = (
            db.query(ProductVariant)
            .options(selectinload(ProductVariant.product).selectinload(Product.variants))
            .filter(
                ProductVariant.is_active == True,  # noqa: E712
                or_(
                    ProductVariant.barcode == raw,
                    ProductVariant.product_code == raw,
                    ProductVariant.sku == raw,
                ),
            )
            .first()
        )
        if matched_variant and matched_variant.product:
            product = matched_variant.product
            if product.is_deleted or not product.is_active or not product.is_approved:
                raise HTTPException(status_code=404, detail="Product not found for the scanned barcode")
    if not product:
        raise HTTPException(
            status_code=404,
            detail="No product matched this barcode. Use numeric product code, P-<id>, SKU, barcode, or product code.",
        )
    return product


def get_recommended_products(current_user: Optional[dict], limit: int, db: Session) -> List[Product]:
    """Return personalised products based on browsing history, fall back to top sellers."""
    import json as _json
    from sqlalchemy.orm import selectinload
    categories: list[str] = []

    if current_user:
        user = (
            db.query(User)
            .filter(User.id == current_user["id"])
            .first()
        )
        browsing_history_json = getattr(user, "browsing_history_json", None) if user else None
        if user and browsing_history_json:
            try:
                history: list[int] = _json.loads(browsing_history_json)[-20:]
                if history:
                    viewed = (
                        db.query(Product)
                        .options(selectinload(Product.variants))
                        .filter(Product.id.in_(history))
                        .all()
                    )
                    categories = list({cast(str, getattr(p, "category")) for p in viewed if cast(str | None, getattr(p, "category"))})
            except Exception:
                pass

    base_q = db.query(Product).filter(
        Product.is_deleted == False,   # noqa: E712
        Product.is_active == True,     # noqa: E712
        Product.is_approved == True,   # noqa: E712
    )

    if categories:
        results = (
            base_q
            .filter(Product.category.in_(categories))
            .order_by(Product.sales_count.desc())
            .limit(limit)
            .all()
        )
        if len(results) >= limit:
            return results
        # Top up with best sellers from other categories
        seen_ids = {p.id for p in results}
        fillers = (
            base_q
            .filter(Product.id.notin_(seen_ids))
            .order_by(Product.sales_count.desc())
            .limit(limit - len(results))
            .all()
        )
        return results + fillers

    return base_q.order_by(Product.sales_count.desc()).limit(limit).all()


# ── Cascade write functions for product deletion (moved from products_write_service) ───

def clear_product_carts(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all cart items for a product during cascade delete."""
    from domains.governance.ports import CartItem
    return _soft_delete_by_product(db, CartItem, product_id)


def clear_product_wishlists(db: Session, product_id: int) -> int:
    """Remove (soft-delete) all wishlist items for a product during cascade delete."""
    from domains.catalog.models.products import WishlistItem
    return _soft_delete_by_product(db, WishlistItem, product_id)


def archive_product_reviews(db: Session, product_id: int) -> int:
    """Soft-delete a product's reviews, preserving the data history."""
    from domains.catalog.models.products import Review
    return _soft_delete_by_product(db, Review, product_id)


def _soft_delete_by_product(db: Session, model, product_id: int) -> int:
    """Soft-delete every (non-deleted) row of *model* for *product_id*."""
    from infrastructure.utils.datetime_utils import utcnow
    updated = (
        db.query(model)
        .filter(model.product_id == product_id, model.is_deleted.is_(False))
        .update(
            {model.is_deleted: True, model.deleted_at: utcnow()},
            synchronize_session=False,
        )
    )
    db.commit()
    return updated


def purge_product_cart_items(db: Session, product_id: int) -> int:
    """Remove every cart row referencing *product_id*. Caller commits."""
    from domains.governance.ports import CartItem
    return (
        db.query(CartItem)
        .filter(CartItem.product_id == product_id)
        .delete(synchronize_session=False)
    )


def purge_product_wishlist_items(db: Session, product_id: int) -> int:
    """Remove every wishlist row referencing *product_id*. Caller commits."""
    from domains.catalog.models.products import Wishlist
    return (
        db.query(Wishlist)
        .filter(Wishlist.product_id == product_id)
        .delete(synchronize_session=False)
    )


def soft_delete_product_reviews(db: Session, product_id: int) -> int:
    """Flag a product's live reviews as deleted. Caller commits."""
    from domains.catalog.models.products import Review
    return (
        db.query(Review)
        .filter(Review.product_id == product_id, Review.is_deleted == False)
        .update({"is_deleted": True}, synchronize_session=False)
    )


def create_product_verification(
    db: Session,
    *,
    product_id: int,
    order_id: Optional[int] = None,
    shipment_id: Optional[int] = None,
    verified_by: Optional[int] = None,
    verification_type: Optional[str] = None,
    result: Optional[str] = None,
    expected_specs: Optional[str] = None,
    actual_specs: Optional[str] = None,
    discrepancies: Optional[str] = None,
    scan_code: Optional[str] = None,
    image_urls: Optional[str] = None,
    notes: Optional[str] = None,
):
    """Persist a new ProductVerification row and return it."""
    from domains.governance.models.admin import ProductVerification
    verification = ProductVerification(
        product_id=product_id,
        order_id=order_id,
        shipment_id=shipment_id,
        verified_by=verified_by,
        verification_type=verification_type,
        result=result,
        expected_specs=expected_specs,
        actual_specs=actual_specs,
        discrepancies=discrepancies,
        scan_code=scan_code,
        image_urls=image_urls,
        notes=notes,
    )
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


def update_product_verification(db: Session, verification, updates: dict):
    """Apply *updates* to an existing verification row and return it."""
    for key, value in updates.items():
        setattr(verification, key, value)
    db.add(verification)
    db.commit()
    db.refresh(verification)
    return verification


# ── Admin Product Read Helpers (merged from product_admin_read_service.py) ───

def _bump_cache() -> None:
    _bump_product_cache_version()


def _scoped_product(db: Session, country_code: str, product_id: int) -> Product:
    """Resolve a product scoped to a country (404 + request RLS)."""
    code = country_code.upper()
    get_country_or_404(code, db)
    set_rls_context({code}, is_restricted=True)
    try:
        product = db.query(Product).filter(Product.id == product_id, Product.country_code == code).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        return product
    finally:
        clear_rls_context()


def list_products_paginated(
    db: Session,
    *,
    country_code: str,
    page: int,
    size: int,
    moderation_status: str | None = None,
    include_deleted: bool = False,
) -> dict:
    """Country-scoped, paginated product list used by the admin catalogue grid."""
    q = db.query(Product).filter(Product.country_code == country_code)
    if moderation_status:
        q = q.filter(Product.moderation_status == moderation_status)
    if not include_deleted:
        q = q.filter(Product.is_deleted == False)
    return paginated_response(q, page, size)


# ── Admin Product Write Helpers (merged from product_admin_write_service.py) ───

def approve_product_by_id(db: Session, country_code: str, product_id: int) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "approved"
    product.is_verified = True
    db.commit()
    _bump_cache()
    return {"message": "Product approved"}


def reject_product_by_id(db: Session, country_code: str, product_id: int, reason: Optional[str] = None) -> dict:
    product = _scoped_product(db, country_code, product_id)
    product.moderation_status = "rejected"
    product.moderation_notes = reason
    db.commit()
    _bump_cache()
    return {"message": "Product rejected"}


def set_product_badge_by_id(db: Session, country_code: str, product_id: int, field: str, value: bool) -> dict:
    if field not in ("is_hot", "is_featured"):
        raise HTTPException(status_code=400, detail="field must be 'is_hot' or 'is_featured'")
    product = _scoped_product(db, country_code, product_id)
    setattr(product, field, value)
    db.commit()
    _bump_cache()
    return {"message": "Product badge updated", "field": field, "value": value}


# ── Product Domain Service (merged from product_service.py) ───

from typing import Mapping
from sqlalchemy.orm import Query
from domains.comms.models.suppliers import SupplierProfile
from infrastructure.utils.slug import generate_slug, generate_slug_hash


class ProductNotFoundError(LookupError):
    """Raised when a product does not exist or is not visible to the caller."""


class SupplierProfileNotFoundError(LookupError):
    """Raised when the acting user has no supplier profile."""


MODERATION_APPROVED = "approved"
MODERATION_REJECTED = "rejected"
MODERATION_PENDING = "pending"

BADGE_FIELDS: frozenset[str] = frozenset({"is_hot", "is_featured"})

_CREATE_FIELDS: frozenset[str] = frozenset({
    "description", "short_description", "sku", "barcode", "price", "compare_price",
    "cost_price", "stock", "low_stock_threshold", "weight", "dimensions", "image_url",
    "images", "category", "subcategory", "category_id", "tags", "attributes", "brand",
    "color", "sizes", "materials", "meta_title", "meta_description", "country_code",
})

_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "short_description", "price", "compare_price", "cost_price",
    "stock", "low_stock_threshold", "weight", "dimensions", "image_url", "images",
    "category", "subcategory", "category_id", "tags", "attributes", "is_active",
    "is_featured", "brand", "color", "sizes", "materials", "rating", "meta_title",
    "meta_description",
})

_SUPPLIER_UPDATE_FIELDS: frozenset[str] = frozenset({
    "name", "description", "price", "stock", "category", "is_active", "tags", "image_url",
})

_FIELD_ALIASES: dict[str, str] = {"stock_quantity": "stock"}


def _normalize(payload: Mapping[str, Any], allowed: frozenset[str]) -> dict[str, Any]:
    resolved: dict[str, Any] = {}
    for key, value in (payload or {}).items():
        canonical = _FIELD_ALIASES.get(key, key)
        if canonical in allowed:
            resolved[canonical] = value
    return resolved


def unique_slug(db: Session, name: str) -> str:
    base = generate_slug(name); slug = base; counter = 1
    while db.query(Product.id).filter(Product.slug == slug).first() is not None:
        slug = f"{base}-{counter}"; counter += 1
    return slug


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_slug_hash(db: Session, slug_hash: str) -> Optional[Product]:
    return db.query(Product).filter(Product.slug_hash == slug_hash).first()


def get_supplier_profile(db: Session, user_id: int) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if profile is None: raise SupplierProfileNotFoundError("Supplier profile not found")
    return profile


def get_supplier_products_query(db: Session, supplier_id: int) -> Query:
    return db.query(Product).filter(Product.supplier_id == supplier_id).order_by(Product.id.desc())


def list_products_for_supplier(db: Session, supplier_id: int) -> Query:
    return get_supplier_products_query(db, supplier_id)


def get_supplier_product(db: Session, product_id: int, supplier_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id).first()


def get_owned_product(db: Session, product_id: int, supplier_id: int, *, exclude_deleted: bool = False) -> Product:
    query = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier_id)
    if exclude_deleted: query = query.filter(Product.is_deleted.is_(False))
    product = query.first()
    if product is None: raise ProductNotFoundError("Product not found")
    return product


def get_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    query = db.query(Product).filter(Product.country_code == country_code.upper())
    if moderation_status: query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted: query = query.filter(Product.is_deleted.is_(False))
    return query.order_by(Product.id.desc())


def list_country_products_query(db: Session, country_code: str, *, moderation_status: Optional[str] = None, include_deleted: bool = False) -> Query:
    query = db.query(Product).filter(Product.country_code == country_code.upper()).order_by(Product.id.desc())
    if moderation_status: query = query.filter(Product.moderation_status == moderation_status)
    if not include_deleted: query = query.filter(Product.is_deleted == False)
    return query


def get_country_product(db: Session, product_id: int, country_code: str) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.country_code == country_code.upper()).first()
    if product is None: raise ProductNotFoundError("Product not found")
    return product


def create_product(db: Session, *, name: str, supplier_id: int, payload: Optional[Mapping[str, Any]] = None, is_active: bool = True, is_featured: bool = False, is_digital: bool = False, is_verified: bool = True, is_approved: bool = True, moderation_status: str = MODERATION_APPROVED) -> Product:
    clean_name = str(name or "").strip()
    if not clean_name: raise ValueError("Product name is required")
    data = _normalize(payload or {}, _CREATE_FIELDS)
    product = Product(name=clean_name, slug=unique_slug(db, clean_name), slug_hash=generate_slug_hash(clean_name), supplier_id=int(supplier_id), price=data.pop("price", None) or 0, stock=data.pop("stock", None) or 0, low_stock_threshold=data.pop("low_stock_threshold", None) or 5, rating=float(data.pop("rating", 0.0) or 0.0), is_active=bool(is_active), is_featured=bool(is_featured), is_digital=bool(is_digital), is_verified=bool(is_verified), is_approved=bool(is_approved), is_deleted=False, moderation_status=str(moderation_status or MODERATION_APPROVED))
    for field, value in data.items(): setattr(product, field, value)
    db.add(product); db.commit(); db.refresh(product)
    logger.info("product.created id=%s supplier_id=%s", product.id, supplier_id)
    return product


def update_product(db: Session, product: Product, updates: Mapping[str, Any], *, allowed_fields: Optional[frozenset[str]] = None, regenerate_slug: bool = True) -> Product:
    data = _normalize(updates, allowed_fields or _UPDATE_FIELDS)
    for field, value in data.items(): setattr(product, field, value)
    if regenerate_slug and data.get("name"): product.slug = unique_slug(db, str(data["name"]))
    db.commit(); db.refresh(product)
    logger.info("product.updated id=%s fields=%s", product.id, sorted(data))
    return product


def update_supplier_product(db: Session, product: Product, updates: Mapping[str, Any]) -> Product:
    return update_product(db, product, updates, allowed_fields=_SUPPLIER_UPDATE_FIELDS, regenerate_slug=False)


def update_product_discount(db: Session, product: Product, *, clear: bool = False, compare_price: Any = ..., discount_starts_at: Any = ..., discount_ends_at: Any = ...) -> Product:
    if clear:
        product.compare_price = None; product.discount_starts_at = None; product.discount_ends_at = None
        db.commit(); db.refresh(product); return product
    if compare_price is not ...: product.compare_price = float(compare_price) if compare_price is not None else None
    if discount_starts_at is not ...: product.discount_starts_at = discount_starts_at
    if discount_ends_at is not ...: product.discount_ends_at = discount_ends_at
    db.commit(); db.refresh(product); return product


def set_product_image(db: Session, product: Product, image_url: str) -> Product:
    product.image_url = image_url; db.commit(); db.refresh(product); return product


def soft_delete_product(db: Session, product: Product, *, deactivate: bool = True) -> Product:
    product.is_deleted = True
    if deactivate: product.is_active = False
    db.commit(); db.refresh(product); return product


def set_moderation_status(db: Session, product: Product, status: str, *, notes: Optional[str] = None) -> Product:
    normalized = str(status or "").lower()
    if normalized not in {MODERATION_APPROVED, MODERATION_REJECTED, MODERATION_PENDING}: raise ValueError(f"Unsupported moderation status: {status!r}")
    product.moderation_status = normalized
    if normalized == MODERATION_APPROVED: product.is_verified = True
    if notes is not None and hasattr(product, "moderation_notes"): product.moderation_notes = notes
    db.commit(); db.refresh(product); return product


def set_product_badge(db: Session, product: Product, field: str, value: bool) -> Product:
    if field not in BADGE_FIELDS: raise ValueError(f"field must be one of {sorted(BADGE_FIELDS)}")
    setattr(product, field, bool(value)); db.commit(); db.refresh(product); return product


def set_product_verified(db: Session, product: Product, value: bool) -> Product:
    product.is_verified = bool(value); db.commit(); db.refresh(product); return product


def _parse_discount_datetime(raw: Any, field: str) -> Optional[datetime]:
    if raw in (None, ""): return None
    try: return datetime.fromisoformat(str(raw)).replace(tzinfo=timezone.utc)
    except (TypeError, ValueError) as exc:
        logger.exception("_parse_discount_datetime_failed", error=str(exc))
        raise HTTPException(status_code=400, detail=f"Invalid {field} format: {raw}") from exc


def build_discount_summary(product: Product, now: datetime) -> dict[str, Any]:
    price = float(product.price or 0)
    compare_price = float(product.compare_price) if product.compare_price is not None else None
    discount_pct = 0.0
    if compare_price and compare_price > 0: discount_pct = round((1 - price / compare_price) * 100, 1)
    active = bool(compare_price and compare_price > price)
    starts_at = product.discount_starts_at; ends_at = product.discount_ends_at
    if starts_at and ends_at: active = active and starts_at <= now <= ends_at
    elif starts_at: active = active and starts_at <= now
    return {"product_id": product.id, "price": price, "compare_price": compare_price, "discount_percentage": discount_pct, "discount_active": active}


def build_image_filename(product_id: int, original_filename: Optional[str]) -> str:
    name = original_filename or "product.jpg"
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "jpg"
    return f"product_{product_id}_{uuid4().hex[:8]}.{ext}"


# ── Supplier Product Functions (merged from supplier_products_service.py) ───

from fastapi import File, UploadFile
from infrastructure.utils.file_validation import validate_upload_image
from infrastructure.utils.storage import storage as _storage
from infrastructure.utils.config import settings
from infrastructure.utils.datetime_utils import utcnow


def list_my_products(page: int, size: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    q = db.query(Product).filter(Product.supplier_id == supplier.id)
    return paginated_response(q, page, size)


def get_supplier_product(product_id: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    return product


def update_product_discount_supplier(product_id: int, payload: dict, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    if payload.get("clear"):
        product.compare_price = None; product.discount_starts_at = None; product.discount_ends_at = None
        db.commit(); db.refresh(product)
        return {"status": "success", "message": "Discount cleared", "product_id": product.id}
    if "compare_price" in payload: product.compare_price = float(payload["compare_price"]) if payload["compare_price"] is not None else None
    if "discount_starts_at" in payload:
        raw = payload["discount_starts_at"]
        try: product.discount_starts_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError): raise HTTPException(400, f"Invalid discount_starts_at format: {raw}")
    if "discount_ends_at" in payload:
        raw = payload["discount_ends_at"]
        try: product.discount_ends_at = datetime.fromisoformat(raw).replace(tzinfo=timezone.utc) if raw else None
        except (ValueError, TypeError): raise HTTPException(400, f"Invalid discount_ends_at format: {raw}")
    db.commit(); db.refresh(product)
    discount_pct = 0; now = utcnow()
    if product.compare_price and product.price and float(product.compare_price) > 0:
        discount_pct = round((1 - float(product.price) / float(product.compare_price)) * 100, 1)
    is_active = bool(product.compare_price and product.compare_price > product.price)
    if product.discount_starts_at and product.discount_ends_at: is_active = is_active and product.discount_starts_at <= now <= product.discount_ends_at
    elif product.discount_starts_at: is_active = is_active and product.discount_starts_at <= now
    return {"status": "success", "product_id": product.id, "price": float(product.price), "compare_price": float(product.compare_price) if product.compare_price else None, "discount_percentage": discount_pct, "discount_active": is_active}


def update_supplier_product_fields(product_id: int, payload: dict, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    field_map = {"name": "name", "description": "description", "price": "price", "stock": "stock", "stock_quantity": "stock", "category": "category", "is_active": "is_active", "tags": "tags", "image_url": "image_url"}
    for key, attr in field_map.items():
        if key in payload: setattr(product, attr, payload[key])
    db.commit(); db.refresh(product)
    return product


async def upload_supplier_product_image(product_id: int, file: UploadFile, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id).first()
    if not product: raise HTTPException(404, "Product not found")
    content = await file.read()
    max_size = getattr(settings, "MAX_UPLOAD_SIZE_MB", 10) * 1024 * 1024
    if len(content) > max_size: raise HTTPException(400, f"File too large (max {getattr(settings, 'MAX_UPLOAD_SIZE_MB', 10)}MB)")
    validate_upload_image(content, file.filename or "product.jpg")
    ext = file.filename.rsplit(".", 1)[-1] if "." in (file.filename or "") else "jpg"
    filename = f"product_{product_id}_{uuid.uuid4().hex[:8]}.{ext}"
    key = f"products/{filename}"
    new_url = _storage.save(key, content, content_type=file.content_type)
    old_url = product.image_url or ""
    if old_url:
        old_key = None
        if old_url.startswith("/uploads/"): old_key = old_url.lstrip("/")
        elif getattr(_storage, "cdn_base", "") and old_url.startswith(_storage.cdn_base): old_key = old_url[len(_storage.cdn_base):].lstrip("/")
        if old_key:
            try: _storage.delete(old_key)
            except Exception: pass
    product.image_url = new_url; db.commit(); db.refresh(product)
    return {"image_url": new_url, "filename": filename, "product_id": product.id}


def delete_supplier_product(product_id: int, current_user, db: Session):
    supplier = db.query(SupplierProfile).filter(SupplierProfile.user_id == current_user.id).first()
    if not supplier: raise HTTPException(404, "Supplier profile not found")
    product = db.query(Product).filter(Product.id == product_id, Product.supplier_id == supplier.id, Product.is_deleted == False).first()
    if not product: raise HTTPException(404, "Product not found")
    product.is_deleted = True; db.commit()
    return {"status": "success", "message": "Product deleted"}


# === RELIABILITY: Health & Metrics ===


def get_products_health() -> dict:
    """Return health status of the products service for monitoring."""
    from infrastructure.database.database import check_connection_health, get_pool_metrics

    db_healthy = check_connection_health()
    pool_metrics = get_pool_metrics()

    return {
        "database": "healthy" if db_healthy else "unhealthy",
        "connection_pool": pool_metrics,
        "cache_version": _get_product_cache_version(),
    }