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
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from models import (
    CartItem, Category, FlashSale, Notification, Order, OrderItem, Product, ProductVariant, Review, SupplierProfile, User, Wishlist, CountryConfig
)
from db.schemas import Product as ProductSchema, ProductCreate
from utils.audit_log import audit_log, AuditAction
from utils.cache import cache_or_compute, cache_get_json, cache_set_json, build_versioned_cache_key
from services.write_helpers import (
    add_and_flush,
    commit_only,
    refresh_only,
)


logger = logging.getLogger(__name__)


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
        from utils.auth import _get_redis
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
    try:
        redis_client = _get_redis_client()
        if redis_client is not None:
            redis_client.incr(_PRODUCT_CACHE_VERSION_KEY)
    except Exception:
        pass


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
    from services.logistics_partner_pricing import normalize_country_code
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
        from services.logistics_partner_pricing import normalize_country_code
        code = normalize_country_code(resolved_country)
        restriction_cache: dict[str, bool] = {}
        if code:
            from models.countries import CountryConfig
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
    data = _prepare_product_write_payload(product.model_dump())
    data = _resolve_product_category_fields(data, db)
    data["name"] = html.escape(data["name"].strip()) if data.get("name") else data.get("name")
    if data.get("description"):
        data["description"] = html.escape(data["description"])
    db_product = Product(**data)
    add_and_flush(db, db_product)
    commit_only(db)
    _bump_product_cache_version()
    refresh_only(db, db_product)
    return db_product


def get_product(product_id: int, db: Session) -> Product:
    cache_key = _build_product_cache_key("detail", {"product_id": product_id})
    cached_payload = _cache_get_json(cache_key)
    if isinstance(cached_payload, dict):
        return cached_payload

    product = db.query(Product).options(selectinload(Product.variants)).filter(
        Product.id == product_id,
        Product.is_deleted == False,  # noqa: E712
    ).first()
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
    commit_only(db)
    _bump_product_cache_version()
    refresh_only(db, db_product)
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
        add_and_flush(db, Notification(
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
    commit_only(db)
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
    commit_only(db)
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
    commit_only(db)
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
            from models import User as UserModel
            from utils.email_service import send_email
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
    from utils.file_validation import validate_upload_image
    from services.storage import storage as _storage

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
    add_and_flush(db, product)
    commit_only(db)
    _bump_product_cache_version()
    refresh_only(db, product)
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
            .options(selectinload(User.browsing_history_json))
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

