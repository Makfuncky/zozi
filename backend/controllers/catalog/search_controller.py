"""
Search Controller — natural-language query parsing and smart product search logic.
"""
import hashlib
import json
import re
from typing import Any, Optional, List, cast

from fastapi.responses import Response
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from models.products import Product
from data.schemas import _normalize_image_path
from utils.cache import build_versioned_cache_key, bump_cache_version, cache_or_compute, cache_set_json, get_cache_version

# ── Price-range keyword map ────────────────────────────────────────────────
PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]] = [
    (re.compile(r"\bcheap\b|\bbudget\b|\baffordable\b", re.I), None, 50.0),
    (re.compile(r"\bmid[- ]?range\b|\bmoderate\b", re.I), 50.0, 200.0),
    (re.compile(r"\bpremium\b|\bluxury\b|\bexpensive\b|\bhigh[- ]?end\b", re.I), 200.0, None),
]

_UNDER_PAT = re.compile(r"\bunder\s+(\d+(?:\.\d+)?)\b", re.I)
_ABOVE_PAT = re.compile(r"\bover\s+(\d+(?:\.\d+)?)\b|\babove\s+(\d+(?:\.\d+)?)", re.I)
_BETWEEN_PAT = re.compile(r"\bbetween\s+(\d+(?:\.\d+)?)\s+(?:and|to|-)\s+(\d+(?:\.\d+)?)\b", re.I)

CATEGORY_SYNONYMS: dict[str, list[str]] = {
    "electronics": ["phone", "laptop", "computer", "tablet", "headphone", "earphone", "camera", "gadget", "tech"],
    "fashion": [
        "cloth", "dress", "shirt", "t-shirt", "tshirt", "tee", "shoes", "shoe", "jeans", "wear", "outfit", "fashion",
        "bra", "bras", "bralette", "lingerie", "underwear", "hoodie", "hoodies", "sweatshirt", "jacket", "coat",
        "leggings", "legging", "pants", "trousers", "shorts", "skirt", "blouse", "top", "sneaker", "sneakers",
    ],
    "home": ["furniture", "decor", "kitchen", "sofa", "bed", "home"],
    "sports": ["sport", "fitness", "gym", "yoga", "exercise", "running"],
    "beauty": ["beauty", "cosmetic", "skincare", "makeup", "perfume"],
    "food": ["food", "snack", "drink", "grocery", "organic"],
    "toys": ["toy", "game", "kids", "children", "play"],
    "books": ["book", "novel", "textbook", "reading"],
}

QUERY_STOPWORDS = {
    "a", "an", "and", "any", "available", "best", "brand", "brands", "buy", "cheapest",
    "detail", "details", "find", "for", "get", "give", "good", "have", "hello", "help", "hey", "hi", "i", "in", "item",
    "items", "latest", "look", "looking", "me", "need", "new", "one", "ones", "option",
    "options", "please", "product", "products", "quality", "recommend", "search", "show",
    "pick", "picks", "similar", "some", "style", "styles", "suggest", "that", "the", "them", "these", "this", "those", "top",
    "want", "with", "you",
}
TEXT_SIZE_VALUE_PAT = re.compile(r"\b(?:size\s+)?(xxxl|xxl|xl|xs|s|m|l|small|medium|large|extra\s+small|extra\s+large)\b", re.I)
NUMERIC_SIZE_VALUE_PAT = re.compile(r"\bsize\s+(\d{2,3})\b", re.I)
SIZE_NORMALIZATION = {
    "extra small": "XS",
    "small": "S",
    "medium": "M",
    "large": "L",
    "extra large": "XL",
    "xs": "XS",
    "s": "S",
    "m": "M",
    "l": "L",
    "xl": "XL",
    "xxl": "XXL",
    "xxxl": "XXXL",
}

REQUEST_PAT = re.compile(
    r"\b(show me|show|find|search|looking for|i want|i need|need|want|give me|recommend|suggest|do you have|you have|"
    r"can you find|help me find|help me choose)\b",
    re.I,
)
FILLER_PAT = re.compile(
    r"\b(options?|products?|items?|ones?|available|please|something|similar|another|more|good|quality|styles?|picks?)\b",
    re.I,
)
QUALITY_PATTERNS: list[tuple[re.Pattern, Optional[float], Optional[str], Optional[str]]] = [
    (re.compile(r"\b(top[- ]?rated|highest\s+rating|well[- ]?reviewed|5\s*star)\b", re.I), 4.0, "rating", "top-rated"),
    (re.compile(r"\b(good\s+quality|high\s+quality|best\s+quality|durable|premium\s+quality)\b", re.I), None, "rating", "quality"),
]
COLOR_ALIASES = {
    "black": "black",
    "white": "white",
    "blue": "blue",
    "red": "red",
    "green": "green",
    "yellow": "yellow",
    "pink": "pink",
    "purple": "purple",
    "brown": "brown",
    "grey": "gray",
    "gray": "gray",
    "silver": "silver",
    "gold": "gold",
    "beige": "beige",
    "orange": "orange",
}
TEXT_SEARCH_FIELDS = (
    Product.name,
    Product.description,
    Product.category,
    Product.brand,
    Product.tags,
    Product.ai_description,
    Product.materials,
)


def _database_supports_postgres_fts(db: Session) -> bool:
    bind = db.get_bind()
    return bool(bind is not None and bind.dialect.name == "postgresql")


def _build_postgres_search_document():
    return Product.search_vector


def _build_postgres_tsquery(parsed: dict[str, Any]):
    phrases: list[str] = []
    cleaned_query = _normalize_query_text(str(parsed.get("q") or ""))
    if cleaned_query:
        phrases.append(cleaned_query)
    if parsed.get("brand"):
        phrases.append(str(parsed["brand"]))
    if parsed.get("color"):
        phrases.append(str(parsed["color"]))
    if parsed.get("size"):
        phrases.append(str(parsed["size"]))
    query_text = " ".join(dict.fromkeys(phrases)).strip()
    if not query_text:
        return None
    return func.websearch_to_tsquery("simple", query_text)


def _normalize_query_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _extract_color(q: str) -> Optional[str]:
    q_lower = q.lower()
    for alias, normalized in COLOR_ALIASES.items():
        if re.search(rf"\b{re.escape(alias)}\b", q_lower):
            return normalized
    return None


def _extract_quality_preferences(q: str) -> tuple[Optional[float], Optional[str], Optional[str]]:
    for pattern, min_rating, sort, quality in QUALITY_PATTERNS:
        if pattern.search(q):
            return min_rating, sort, quality
    return None, None, None


def _normalize_size_value(raw_size: str) -> str:
    normalized = re.sub(r"\s+", " ", raw_size.strip().lower())
    return SIZE_NORMALIZATION.get(normalized, raw_size.strip().upper())


def _extract_size(q: str) -> Optional[str]:
    numeric_match = NUMERIC_SIZE_VALUE_PAT.search(q)
    if numeric_match:
        return _normalize_size_value(numeric_match.group(1))

    text_match = TEXT_SIZE_VALUE_PAT.search(q)
    if not text_match:
        return None
    return _normalize_size_value(text_match.group(1))


def _extract_terms(clean_q: str) -> list[str]:
    terms: list[str] = []
    for token in re.findall(r"[a-z0-9]+", clean_q.lower().replace("-", " ")):
        if len(token) <= 1 or token in QUERY_STOPWORDS:
            continue
        terms.append(token)
        if token.endswith("s") and len(token) > 3:
            singular = token[:-1]
            if singular not in QUERY_STOPWORDS:
                terms.append(singular)
    return list(dict.fromkeys(terms))


def _strip_phrase(text: str, phrase: str) -> str:
    if not phrase:
        return text
    return _normalize_query_text(re.sub(rf"\b{re.escape(phrase)}\b", " ", text, flags=re.I))


def _deserialize_sizes(raw_sizes: Any) -> list[str]:
    if not raw_sizes:
        return []
    if isinstance(raw_sizes, list):
        return [str(item).strip() for item in raw_sizes if str(item).strip()]
    if isinstance(raw_sizes, str):
        try:
            parsed = json.loads(raw_sizes)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
        return [item.strip() for item in raw_sizes.split(",") if item.strip()]
    return []


def _resolve_brand_from_catalog(parsed: dict[str, Any], db: Session) -> dict[str, Any]:
    if parsed.get("brand"):
        return parsed

    raw_query = str(parsed.get("raw_q") or parsed.get("q") or "").lower()
    if not raw_query:
        return parsed

    q_digest = hashlib.sha1(raw_query.encode()).hexdigest()
    brand_cache_key = f"search:brand_catalog:{q_digest}"

    def _fetch_brands() -> list[str]:
        brand_rows = (
            db.query(Product.brand)
            .filter(
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,  # noqa: E712
                Product.is_approved == True,  # noqa: E712
                Product.stock > 0,
                Product.brand.isnot(None),
            )
            .distinct()
            .all()
        )
        return sorted(
            [cast(str, row[0]).strip() for row in brand_rows if row and row[0]],
            key=len,
            reverse=True,
        )

    brands = cache_or_compute(key=brand_cache_key, compute=_fetch_brands, ttl=300, namespace="products:search")
    for brand in brands:
        if re.search(rf"\b{re.escape(brand.lower())}\b", raw_query):
            updated = dict(parsed)
            updated["brand"] = brand
            updated["q"] = _strip_phrase(str(updated.get("q") or ""), brand)
            updated["terms"] = [term for term in cast(list[str], updated.get("terms") or []) if term not in _extract_terms(brand)]
            return updated
    return parsed


def _serialize_product(product: Product) -> dict[str, Any]:
    image_url = cast(str | None, getattr(product, "image_url"))
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "rating": product.rating,
        "brand": getattr(product, "brand", None),
        "image_url": _normalize_image_path(image_url),
        "category": product.category,
        "stock": product.stock,
        "color": getattr(product, "color", None),
        "sizes": _deserialize_sizes(getattr(product, "sizes", None)),
    }


def _serialize_recommendation_product(product: Product) -> dict[str, Any]:
    image_url = cast(str | None, getattr(product, "image_url"))
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "rating": product.rating,
        "image_url": _normalize_image_path(image_url),
        "category": product.category,
        "stock": product.stock,
    }


def _product_search_blob(product: Product) -> str:
    return " ".join(
        part
        for part in [
            cast(str | None, getattr(product, "name")),
            cast(str | None, getattr(product, "description")),
            cast(str | None, getattr(product, "category")),
            cast(str | None, getattr(product, "brand")),
            cast(str | None, getattr(product, "tags")),
            cast(str | None, getattr(product, "ai_description")),
            cast(str | None, getattr(product, "materials")),
            cast(str | None, getattr(product, "color")),
            cast(str | None, getattr(product, "sizes")),
        ]
        if part
    ).lower()


def _score_product(product: Product, parsed: dict[str, Any], shopper_profile: Optional[dict[str, Any]] = None) -> float:
    blob = _product_search_blob(product)
    name = (cast(str | None, getattr(product, "name")) or "").lower()
    category = (cast(str | None, getattr(product, "category")) or "").lower()
    brand = (cast(str | None, getattr(product, "brand")) or "").lower()
    color = (cast(str | None, getattr(product, "color")) or "").lower()
    sizes = [size.lower() for size in _deserialize_sizes(getattr(product, "sizes", None))]
    score = 0.0

    query_text = cast(str, parsed.get("q") or "").lower()
    if query_text:
        if query_text in name:
            score += 12
        elif query_text in blob:
            score += 8

    for term in cast(list[str], parsed.get("terms") or []):
        if term in name:
            score += 4
        elif term in blob:
            score += 1.5

    requested_color = cast(str | None, parsed.get("color"))
    if requested_color:
        if requested_color == color:
            score += 5
        elif requested_color in blob:
            score += 2

    requested_category = cast(str | None, parsed.get("category"))
    if requested_category and requested_category in category:
        score += 3

    requested_brand = cast(str | None, parsed.get("brand"))
    if requested_brand:
        if requested_brand.lower() == brand:
            score += 6
        elif requested_brand.lower() in blob:
            score += 2.5

    requested_size = cast(str | None, parsed.get("size"))
    if requested_size:
        normalized_size = requested_size.lower()
        if normalized_size in sizes:
            score += 4
        elif normalized_size in blob:
            score += 1.5

    if shopper_profile:
        preferred_categories = {str(value).lower() for value in cast(list[str], shopper_profile.get("preferred_categories") or [])}
        preferred_brands = {str(value).lower() for value in cast(list[str], shopper_profile.get("preferred_brands") or [])}
        preferred_price = cast(Optional[float], shopper_profile.get("preferred_price"))
        price = float(cast(Any, getattr(product, "price")) or 0)

        if not requested_category and category in preferred_categories:
            score += 1.75
        if not requested_brand and brand and brand in preferred_brands:
            score += 2.0
        if preferred_price and parsed.get("min_price") is None and parsed.get("max_price") is None and price > 0:
            score += max(0.0, 2.0 - abs(price - preferred_price) / max(preferred_price, 1.0))

    score += float(cast(float | None, getattr(product, "rating")) or 0)
    score += min(float(cast(int | None, getattr(product, "sales_count")) or 0), 200.0) / 100.0
    return score


def _sort_ranked_products(ranked: list[tuple[float, Product]], parsed: dict[str, Any], limit: int) -> list[Product]:
    sort = parsed.get("sort")
    if sort == "price_asc":
        ranked.sort(
            key=lambda row: (
                float(cast(Any, getattr(row[1], "price")) or 0),
                -row[0],
                -float(cast(Any, getattr(row[1], "rating")) or 0),
            )
        )
    elif sort == "newest":
        ranked.sort(
            key=lambda row: (
                -int(getattr(getattr(row[1], "created_at", None), "timestamp", lambda: 0)()),
                -row[0],
            )
        )
    else:
        ranked.sort(
            key=lambda row: (
                -row[0],
                -float(cast(Any, getattr(row[1], "rating")) or 0),
                -int(cast(Any, getattr(row[1], "sales_count")) or 0),
                float(cast(Any, getattr(row[1], "price")) or 0),
            )
        )
    return [product for _, product in ranked[:limit]]


def parse_query(q: str) -> dict:
    """Extract structured filters from a natural-language product query."""
    result: dict = {
        "raw_q": q,
        "q": q,
        "terms": [],
        "min_price": None,
        "max_price": None,
        "category": None,
        "brand": None,
        "size": None,
        "color": None,
        "min_rating": None,
        "quality": None,
        "sort": None,
    }

    m_between = _BETWEEN_PAT.search(q)
    m_under = _UNDER_PAT.search(q)
    m_above = _ABOVE_PAT.search(q)

    if m_between:
        result["min_price"] = float(m_between.group(1))
        result["max_price"] = float(m_between.group(2))
    elif m_under:
        result["max_price"] = float(m_under.group(1))
    elif m_above:
        result["min_price"] = float(m_above.group(1) or m_above.group(2))

    if result["min_price"] is None and result["max_price"] is None:
        for pat, lo, hi in PRICE_KEYWORDS:
            if pat.search(q):
                result["min_price"] = lo
                result["max_price"] = hi
                break

    min_rating, quality_sort, quality = _extract_quality_preferences(q)
    result["min_rating"] = min_rating
    result["quality"] = quality

    q_lower = q.lower()
    for category, keywords in CATEGORY_SYNONYMS.items():
        if any(kw in q_lower for kw in keywords):
            result["category"] = category
            break

    result["size"] = _extract_size(q)
    result["color"] = _extract_color(q)

    if re.search(r"\bbest\b|\btop[- ]?rated\b|\bhighest\s+rating\b", q, re.I):
        result["sort"] = "rating"
    elif re.search(r"\bnewest\b|\blatest\b|\bnew\b", q, re.I):
        result["sort"] = "newest"
    elif re.search(r"\bcheapest\b|\blowest\s+price\b", q, re.I):
        result["sort"] = "price_asc"
    elif quality_sort:
        result["sort"] = quality_sort

    clean_q = _BETWEEN_PAT.sub("", q)
    clean_q = _UNDER_PAT.sub("", clean_q)
    clean_q = _ABOVE_PAT.sub("", clean_q)
    clean_q = REQUEST_PAT.sub(" ", clean_q)
    clean_q = re.sub(r"\b(hi|hello|hey|please|can you|could you)\b", " ", clean_q, flags=re.I)
    clean_q = re.sub(
        r"\b(any|some|the|a|an|cheap|budget|affordable|mid[- ]?range|premium|luxury|expensive|high[- ]?end|"
        r"best|top[- ]?rated|newest|latest|cheapest|in stock)\b",
        " ",
        clean_q,
        flags=re.I,
    )
    clean_q = FILLER_PAT.sub(" ", clean_q)
    for alias in COLOR_ALIASES:
        clean_q = re.sub(rf"\b{re.escape(alias)}\b", " ", clean_q, flags=re.I)
    if result["size"]:
        clean_q = re.sub(rf"\b(?:size\s+)?{re.escape(cast(str, result['size']))}\b", " ", clean_q, flags=re.I)
    for pattern, _min_rating, _sort, _quality in QUALITY_PATTERNS:
        clean_q = pattern.sub(" ", clean_q)
    clean_q = _normalize_query_text(clean_q.replace("-", " "))
    result["q"] = clean_q or q
    result["terms"] = _extract_terms(clean_q or q)
    return result


def smart_search_from_parsed(
    parsed: dict,
    limit: int,
    db: Session,
    response: Optional[Response] = None,
    shopper_profile: Optional[dict[str, Any]] = None,
    supplier_id: Optional[int] = None,
) -> dict:
    parsed = {
        "raw_q": parsed.get("raw_q") or parsed.get("q") or "",
        "q": _normalize_query_text(cast(str, parsed.get("q") or "")),
        "terms": list(dict.fromkeys(cast(list[str], parsed.get("terms") or _extract_terms(cast(str, parsed.get("q") or ""))))),
        "min_price": parsed.get("min_price"),
        "max_price": parsed.get("max_price"),
        "category": parsed.get("category"),
        "brand": parsed.get("brand"),
        "size": parsed.get("size"),
        "color": parsed.get("color"),
        "min_rating": parsed.get("min_rating"),
        "quality": parsed.get("quality"),
        "sort": parsed.get("sort"),
        "has_video": parsed.get("has_video"),
    }
    parsed = _resolve_brand_from_catalog(parsed, db)

    query = db.query(Product).filter(
        Product.is_deleted == False,
        Product.is_active.isnot(False),
        Product.is_approved.isnot(False),
        Product.stock > 0,
    )

    if supplier_id is not None:
        query = query.filter(Product.supplier_id == supplier_id)

    if parsed["category"]:
        query = query.filter(Product.category.ilike(f"%{parsed['category']}%"))
    if parsed["brand"]:
        query = query.filter(Product.brand.ilike(f"%{parsed['brand']}%"))
    if parsed["color"]:
        color_term = f"%{parsed['color']}%"
        query = query.filter(
            Product.color.ilike(color_term)
            | Product.name.ilike(color_term)
            | Product.description.ilike(color_term)
            | Product.tags.ilike(color_term)
        )
    if parsed["size"]:
        size_term = cast(str, parsed["size"])
        query = query.filter(
            Product.sizes.ilike(f'%"{size_term}"%')
            | Product.sizes.ilike(f"%{size_term}%")
        )
    if parsed["min_price"] is not None:
        query = query.filter(Product.price >= parsed["min_price"])
    if parsed["max_price"] is not None:
        query = query.filter(Product.price <= parsed["max_price"])
    if parsed["min_rating"] is not None:
        query = query.filter(Product.rating >= parsed["min_rating"])

    if parsed.get("has_video"):
        query = query.filter(Product.video_count > 0)

    text_conditions = []
    if parsed["q"]:
        phrase = f"%{parsed['q'].lower()}%"
        text_conditions.extend(field.ilike(phrase) for field in TEXT_SEARCH_FIELDS)
    for term in parsed["terms"][:6]:
        token = f"%{term}%"
        text_conditions.extend(field.ilike(token) for field in TEXT_SEARCH_FIELDS)

    fts_rank = None
    if _database_supports_postgres_fts(db):
        ts_query = _build_postgres_tsquery(parsed)
        if ts_query is not None:
            search_document = _build_postgres_search_document()
            fts_rank = func.ts_rank_cd(search_document, ts_query)
            fts_match = search_document.op("@@")(ts_query)
            if text_conditions:
                query = query.filter(or_(fts_match, *text_conditions))
            else:
                query = query.filter(fts_match)
    elif text_conditions:
        query = query.filter(or_(*text_conditions))

    order_by = []
    if fts_rank is not None:
        order_by.append(desc(fts_rank))
    order_by.extend([
        Product.sales_count.desc(),
        Product.rating.desc(),
        Product.created_at.desc(),
    ])

    candidates = query.order_by(*order_by).limit(max(limit * 12, 48)).all()

    ranked = [(_score_product(product, parsed, shopper_profile=shopper_profile), product) for product in candidates]
    products = _sort_ranked_products(ranked, parsed, limit)

    if response is not None:
        response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=60"

    normalized_products = [_serialize_product(product) for product in products]

    return {
        "parsed": {
            "q": parsed["q"],
            "terms": parsed["terms"],
            "category": parsed["category"],
            "brand": parsed["brand"],
            "size": parsed["size"],
            "color": parsed["color"],
            "min_price": parsed["min_price"],
            "max_price": parsed["max_price"],
            "min_rating": parsed["min_rating"],
            "quality": parsed["quality"],
            "sort": parsed["sort"],
        },
        # Keep both keys for backward compatibility across existing web/mobile clients.
        "products": normalized_products,
        "results": normalized_products,
    }


def smart_search(
    q: str,
    limit: int,
    db: Session,
    response: Optional[Response] = None,
    supplier_id: Optional[int] = None,
) -> dict:
    parsed = parse_query(q)
    return smart_search_from_parsed(
        parsed=parsed,
        limit=limit,
        db=db,
        response=response,
        supplier_id=supplier_id,
    )


def get_recommendations(
    user_id: Optional[int],
    db: Session,
    limit: int = 8,
    recent_categories: Optional[list[str]] = None,
) -> dict:
    """
    Lightweight preference algorithm with Redis response cache (TTL 5 min):
    1) Build category preference from purchased quantities.
    2) Blend wishlist product categories (0.3 pts each, lower than purchase signal).
    3) Blend recent browsing categories from frontend (0.5 pts each).
    4) Price-preference soft sort — products near the user's average spend surface first.
    5) Item-item "also bought" collaborative signal (+0.2 pts per co-purchase).
    6) Recommend in-stock active products from top categories, excluding purchased items.
    """
    normalized_recent_categories = [
        category.strip()
        for category in (recent_categories or [])
        if category and category.strip()
    ]

    if user_id is None:
        query = db.query(Product).filter(
            Product.is_deleted == False,   # noqa: E712
            Product.is_active.isnot(False),
            Product.is_approved.isnot(False),
            Product.stock > 0,
        )
        if normalized_recent_categories:
            query = query.filter(Product.category.in_(normalized_recent_categories))

        recommended = query.order_by(Product.sales_count.desc(), Product.rating.desc()).limit(limit).all()
        if not recommended and normalized_recent_categories:
            recommended = (
                db.query(Product)
                .filter(
                    Product.is_deleted == False,   # noqa: E712
                    Product.is_active == True,     # noqa: E712
                    Product.is_approved == True,   # noqa: E712
                    Product.stock > 0,
                )
                .order_by(Product.sales_count.desc(), Product.rating.desc())
                .limit(limit)
                .all()
            )

        results = [_serialize_recommendation_product(product) for product in recommended]
        return {
            "source_categories": normalized_recent_categories[:4],
            "products": results,
            "results": results,
        }

    # ── Redis cache lookup ────────────────────────────────────────────────────
    _cats_key = ",".join(sorted(normalized_recent_categories))
    _cache_key = f"rec:{user_id}:{limit}:{hash(_cats_key)}"

    def _compute_payload() -> dict:
        category_rows = (
            db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
            .join(OrderItem, OrderItem.product_id == Product.id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(
                Order.user_id == user_id,
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,    # noqa: E712
                Product.is_approved == True,  # noqa: E712
            )
            .group_by(Product.category)
            .order_by(desc(func.sum(OrderItem.quantity)))
            .all()
        )
        weighted_categories: dict[str, float] = {
            (row.category or "Uncategorized"): float(row.units or 0)
            for row in category_rows
        }

        # Wishlist signal — each wishlisted product contributes 0.3 pts to its category
        wishlist_rows = (
            db.query(Product.category)
            .join(Wishlist, Wishlist.product_id == Product.id)
            .filter(
                Wishlist.user_id == user_id,
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,    # noqa: E712
            )
            .all()
        )
        for row in wishlist_rows:
            cat = (row.category or "Uncategorized").strip()
            if cat:
                weighted_categories[cat] = weighted_categories.get(cat, 0) + 0.3

        for category in normalized_recent_categories:
            clean = (category or "").strip()
            if clean:
                weighted_categories[clean] = weighted_categories.get(clean, 0) + 0.5

        # Item-item collaborative signal ("also bought"):
        # For each product this user purchased, find other products that appear in the
        # same orders from *other* users, and boost those products' categories.
        # Capped at 20 seed products and 50 co-purchase rows for performance.
        user_product_ids_subq = (
            db.query(OrderItem.product_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.user_id == user_id)
            .distinct()
            .limit(20)
            .scalar_subquery()
        )
        # Orders that contain any of the user's purchased products, placed by other users
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
        # Products bought in those co-orders (excluding this user's own items)
        also_bought_rows = (
            db.query(Product.category, func.count(OrderItem.product_id).label("co_count"))
            .join(OrderItem, OrderItem.product_id == Product.id)
            .filter(
                OrderItem.order_id.in_(co_order_ids_subq),
                Product.id.notin_(user_product_ids_subq),
                Product.is_deleted == False,  # noqa: E712
                Product.is_active == True,    # noqa: E712
                Product.is_approved == True,  # noqa: E712
            )
            .group_by(Product.category)
            .limit(50)
            .all()
        )
        for row in also_bought_rows:
            cat = (row.category or "Uncategorized").strip()
            if cat:
                # 0.2 pts per co-purchase occurrence, capped at 3.0 pts from this signal
                boost = min(float(row.co_count) * 0.2, 3.0)
                weighted_categories[cat] = weighted_categories.get(cat, 0) + boost

        # Price-preference signal — compute user's typical spend band from purchase history
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

        top_categories = [
            category
            for category, _score in sorted(
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
            Product.is_deleted == False,   # noqa: E712
            Product.is_active == True,     # noqa: E712
            Product.is_approved == True,   # noqa: E712
            Product.stock > 0,
        )
        if purchased_product_ids:
            query = query.filter(Product.id.notin_(purchased_product_ids))
        if top_categories:
            query = query.filter(Product.category.in_(top_categories))

        recommended = query.order_by(Product.sales_count.desc(), Product.rating.desc()).limit(limit).all()
        if not recommended:
            # Fallback to global best products when category affinity is sparse.
            fallback_query = db.query(Product).filter(
                Product.is_deleted == False,   # noqa: E712
                Product.is_active == True,     # noqa: E712
                Product.is_approved == True,   # noqa: E712
                Product.stock > 0,
            )
            if purchased_product_ids:
                fallback_query = fallback_query.filter(Product.id.notin_(purchased_product_ids))
            recommended = fallback_query.order_by(Product.sales_count.desc(), Product.rating.desc()).limit(limit).all()

        # Apply price-preference soft sort — in-band items surface first, preserving existing order within each group
        if price_band_lo is not None:
            def _out_of_band(p: Product) -> int:
                prc = float(cast(Any, getattr(p, "price")) or 0)
                return 0 if price_band_lo <= prc <= price_band_hi else 1  # type: ignore[operator]
            recommended = sorted(recommended, key=_out_of_band)

        results = [_serialize_recommendation_product(product) for product in recommended]
        payload = {
            "source_categories": top_categories,
            "products": results,
            "results": results,
        }
        return payload

    return cache_or_compute(
        key=_cache_key,
        compute=_compute_payload,
        ttl=300,
        namespace="products:search",
    )

