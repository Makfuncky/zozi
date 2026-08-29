"""
Search Controller — natural-language query parsing and smart product search logic.
"""
import cachetools
import hashlib
import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher, get_close_matches
from typing import Any, Dict, Optional, List, cast

# In-memory search index used by load_search_catalog (dev/test fallback).
_SEARCH_INDEX: Dict[str, Dict[str, dict]] = {}

from fastapi.responses import Response
from sqlalchemy import desc, func, or_, and_, text, cast as sql_cast, String
from sqlalchemy.orm import Session

from domains.catalog.models.products import Product
from infrastructure.utils.cache import build_versioned_cache_key, bump_cache_version, cache_or_compute, cache_set_json, get_cache_version
from infrastructure.utils.performance_cache import cache_search_results, set_search_results, invalidate_product_listings

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

    # Check search results cache first
    query_hash = hashlib.sha1(json.dumps(parsed, sort_keys=True, default=str).encode()).hexdigest()
    cached_results = cache_search_results(query_hash, 1, limit)
    if cached_results is not None:
        if response is not None:
            response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=60"
            response.headers["X-Cache"] = "HIT"
        return cached_results

    result = smart_search_from_parsed(
        parsed=parsed,
        limit=limit,
        db=db,
        response=response,
        supplier_id=supplier_id,
    )

    # Cache the search results
    set_search_results(query_hash, 1, limit, result)

    if response is not None:
        response.headers["X-Cache"] = "MISS"

    return result


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
    # NOTE: use hashlib (not builtin hash()) for the cache key — builtin hash()
    # is randomized per-process (PYTHONHASHSEED), which would make the key
    # different on every restart and orphan the previously cached entry in Redis.
    _cats_key = ",".join(sorted(normalized_recent_categories))
    _digest = hashlib.md5(_cats_key.encode("utf-8")).hexdigest()
    _cache_key = f"rec:{user_id}:{limit}:{_digest}"

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


# ── Advanced Filter Service (merged from advanced_filter_service.py) ───

from domains.catalog.models.products import ProductVideo, ProductFilterMetadata, ProductFilterOption


class AdvancedFilterService:
    _cache_ttl = 300

    def __init__(self, db: Session):
        self.db = db
        self._cache_version = 0
        self._cache: Dict[str, Dict[str, Any]] = cachetools.TTLCache(maxsize=500, ttl=300)

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
        base_query = self.db.query(Product).filter(Product.is_deleted == False, Product.is_active == True, Product.is_approved == True, Product.stock > 0)
        if category_id is not None:
            base_query = base_query.filter(Product.category_id == category_id)
        if search_query:
            like = f"%{search_query.lower()}%"
            base_query = base_query.filter(or_(Product.name.ilike(like), Product.description.ilike(like), Product.category.ilike(like), Product.brand.ilike(like), cast(Product.tags, String).like(like)))
        price_stats = self._get_price_stats(base_query)
        brands = self._get_brands(base_query)
        ratings = self._get_ratings(base_query)
        attributes = self._get_filter_metadata(category_id, base_query)
        video_count = self._get_video_count(base_query)
        discount_count = self._get_discount_count(base_query)
        result = {"price_range": price_stats, "brands": brands, "ratings": ratings, "attributes": attributes, "video_count": video_count, "discount": discount_count}
        self._cache[cache_key] = result
        return result

    def get_active_filters_summary(self, category_id: Optional[int] = None, search_query: Optional[str] = None) -> Dict[str, Any]:
        base_query = self.db.query(Product).filter(Product.is_deleted == False, Product.is_active == True, Product.is_approved == True, Product.stock > 0)
        if category_id is not None:
            base_query = base_query.filter(Product.category_id == category_id)
        if search_query:
            like = f"%{search_query.lower()}%"
            base_query = base_query.filter(or_(Product.name.ilike(like), Product.description.ilike(like), Product.category.ilike(like), Product.brand.ilike(like), cast(Product.tags, String).like(like)))
        return {"total_products": base_query.count(), "has_video": base_query.filter(Product.video_count > 0).count(), "has_discount": base_query.filter(Product.compare_price.isnot(None), Product.compare_price > Product.price).count(), "in_stock": base_query.filter(Product.stock > 0).count()}

    def apply_filters(self, q, filters: Dict[str, Any]):
        if filters.get("min_price") is not None:
            try: q = q.filter(Product.price >= float(filters["min_price"]))
            except (TypeError, ValueError): pass
        if filters.get("max_price") is not None:
            try: q = q.filter(Product.price <= float(filters["max_price"]))
            except (TypeError, ValueError): pass
        brands = filters.get("brands")
        if brands and isinstance(brands, list): q = q.filter(Product.brand.in_(brands))
        if filters.get("min_rating") is not None:
            try: q = q.filter(Product.rating >= float(filters["min_rating"]))
            except (TypeError, ValueError): pass
        if filters.get("max_rating") is not None:
            try: q = q.filter(Product.rating <= float(filters["max_rating"]))
            except (TypeError, ValueError): pass
        attributes = filters.get("attributes")
        if isinstance(attributes, dict):
            for attr_key, attr_values in attributes.items():
                if not attr_values: continue
                if isinstance(attr_values, list) and attr_values:
                    q = q.filter(and_(Product.filter_attributes.has_key(attr_key), cast(Product.filter_attributes[attr_key], String).in_([str(v) for v in attr_values])))
        if filters.get("has_video") is True: q = q.filter(Product.video_count > 0)
        if filters.get("has_discount") is True: q = q.filter(Product.compare_price.isnot(None), Product.compare_price > Product.price)
        if filters.get("in_stock") is True: q = q.filter(Product.stock > 0)
        if filters.get("new_arrivals") is True:
            from datetime import timedelta
            cutoff = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=60)
            q = q.filter(Product.created_at >= cutoff)
        if filters.get("best_sellers") is True: q = q.filter(Product.sales_count >= 5)
        if filters.get("trending") is True: q = q.filter(Product.sales_count >= 1).order_by(Product.sales_count.desc())
        return q

    def get_filtered_products(self, filters: Dict[str, Any], limit: int = 20, offset: int = 0, cursor: Optional[int] = None) -> Dict[str, Any]:
        cache_key = self._get_cache_key(None, None, filters)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            if isinstance(cached, dict) and "products" in cached: return cached
        query = self.db.query(Product).filter(Product.is_deleted == False, Product.is_active == True, Product.is_approved == True, Product.stock > 0)
        query = self.apply_filters(query, filters)
        total = query.count()
        if cursor:
            query = query.filter(Product.id < cursor)
        products = query.order_by(Product.id.desc()).limit(limit).all()
        result = {"products": [self._serialize_product(p) for p in products], "total": total, "limit": limit, "offset": offset}
        self._cache[cache_key] = result
        return result

    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        return {"id": product.id, "name": product.name, "price": float(product.price) if product.price else 0, "rating": float(product.rating) if product.rating else 0, "brand": product.brand, "category": product.category, "image_url": product.image_url, "stock": product.stock, "video_count": product.video_count or 0}

    def build_search_vector(self, product: Product) -> Dict[str, Any]:
        return {"name": product.name, "description": product.description, "category": product.category, "brand": product.brand, "tags": product.tags, "ai_description": product.ai_description, "materials": product.materials, "color": product.color, "sizes": getattr(product, "sizes", None)}

    def _get_price_stats(self, base_query) -> Dict[str, float]:
        result = base_query.with_entities(func.min(Product.price).label("min_price"), func.max(Product.price).label("max_price"), func.avg(Product.price).label("avg_price")).first()
        return {"min": float(result.min_price) if result.min_price is not None else 0, "max": float(result.max_price) if result.max_price is not None else 0, "avg": float(result.avg_price) if result.avg_price is not None else 0}

    def _get_brands(self, base_query) -> List[Dict[str, Any]]:
        rows = base_query.with_entities(Product.brand, func.count(Product.id).label("count")).filter(Product.brand.isnot(None), Product.brand != "").group_by(Product.brand).order_by(func.count(Product.id).desc()).limit(50).all()
        return [{"brand": row.brand, "count": int(row.count)} for row in rows]

    def _get_ratings(self, base_query) -> List[Dict[str, Any]]:
        distribution: Dict[str, int] = {}
        for rating_low, rating_high, label in [(4.0, 5.0, "4_stars"), (3.0, 4.0, "3_stars"), (2.0, 3.0, "2_stars"), (1.0, 2.0, "1_star")]:
            count = base_query.filter(Product.rating >= rating_low, Product.rating < rating_high).count()
            distribution[label] = count
        return [{"min_rating": 4, "label": "4★ & up", "count": distribution.get("4_stars", 0)}, {"min_rating": 3, "label": "3★ & up", "count": distribution.get("3_stars", 0)}, {"min_rating": 2, "label": "2★ & up", "count": distribution.get("2_stars", 0)}, {"min_rating": 1, "label": "1★ & up", "count": distribution.get("1_star", 0)}]

    def _get_filter_metadata(self, category_id: Optional[int], base_query) -> List[Dict[str, Any]]:
        metadata_query = self.db.query(ProductFilterMetadata)
        if category_id is not None:
            metadata_query = metadata_query.filter(ProductFilterMetadata.category_id == category_id)
        else:
            metadata_query = metadata_query.filter(ProductFilterMetadata.category_id.is_(None))
        metadata = metadata_query.filter(ProductFilterMetadata.is_active == True).all()
        meta_ids = [m.id for m in metadata]
        options_by_meta: dict[int, list[ProductFilterOption]] = {}
        if meta_ids:
            all_options = self.db.query(ProductFilterOption).filter(ProductFilterOption.filter_metadata_id.in_(meta_ids)).order_by(ProductFilterOption.sort_order).all()
            for opt in all_options:
                options_by_meta.setdefault(opt.filter_metadata_id, []).append(opt)
        filters: List[Dict[str, Any]] = []
        for meta in metadata:
            options = options_by_meta.get(meta.id, [])
            filters.append({"id": meta.id, "name": meta.filter_name, "type": meta.filter_type, "display_order": meta.display_order, "options": [{"value": opt.option_value, "display": opt.option_display_name, "count": opt.product_count} for opt in options]})
        return filters

    def _get_video_count(self, base_query) -> Dict[str, int]:
        return {"with_video": base_query.filter(Product.video_count > 0).count()}

    def _get_discount_count(self, base_query) -> Dict[str, Any]:
        discount_products = base_query.filter(Product.compare_price.isnot(None), Product.compare_price > Product.price).count()
        return {"with_discount": discount_products}


# ── Advanced Search Engine (merged from advanced_search_engine.py) ───

_MAX_PAGE_SIZE = 100
_MAX_FUZZY_PRODUCTS = 5000


class AdvancedSearchEngine:
    def __init__(self, db: Session):
        self.db = db
        self._is_postgres = self.db.bind.dialect.name == "postgresql"

    def parse_query(self, query: str) -> Dict[str, Any]:
        parsed: Dict[str, Any] = {"q": query, "terms": [], "min_price": None, "max_price": None, "category": None, "brand": None, "brands": None, "size": None, "color": None, "min_rating": None, "max_rating": None, "sort": None, "has_video": False}
        q_lower = query.lower()
        price_patterns = [(r"\bunder\s+\$?(\d+(?:\.\d+)?)", "max_price"), (r"\bbelow\s+\$?(\d+(?:\.\d+)?)", "max_price"), (r"\bless\s+than\s+\$?(\d+(?:\.\d+)?)", "max_price"), (r"\babove\s+\$?(\d+(?:\.\d+)?)", "min_price"), (r"\bover\s+\$?(\d+(?:\.\d+)?)", "min_price"), (r"\bbetween\s+\$?(\d+(?:\.\d+)?)\s+and\s+\$?(\d+(?:\.\d+)?)", "range_price")]
        for pattern, field in price_patterns:
            match = re.search(pattern, q_lower)
            if match:
                if field == "range_price":
                    parsed["min_price"] = float(match.group(1)); parsed["max_price"] = float(match.group(2))
                elif field == "max_price": parsed["max_price"] = float(match.group(1))
                elif field == "min_price": parsed["min_price"] = float(match.group(1))
                query = re.sub(pattern, "", query, flags=re.IGNORECASE); break
        rating_match = re.search(r"(\d)\+\s*star", q_lower)
        if rating_match: parsed["min_rating"] = int(rating_match.group(1)); query = re.sub(r"(\d)\+\s*star", "", query, flags=re.IGNORECASE)
        brands = ["nike", "adidas", "apple", "samsung", "sony", "lg", "hp", "dell", "canon", "nikon"]
        found_brands = [b.capitalize() for b in brands if b in q_lower]
        if found_brands: parsed["brands"] = found_brands
        if "video" in q_lower or "with video" in q_lower: parsed["has_video"] = True
        if re.search(r"\bnew(est)?\b", q_lower): parsed["sort"] = "newest"; query = re.sub(r"\bnew(est)?\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\b(top|rated|reviewed)\b", q_lower): parsed["sort"] = "rating"; query = re.sub(r"\b(top|rated|reviewed)\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\b(cheap\w*|low(\s*price)?)\b", q_lower): parsed["sort"] = "price_asc"; query = re.sub(r"\b(cheapest|cheap|low\s*price)\b", "", query, flags=re.IGNORECASE)
        elif re.search(r"\bexpensive\b", q_lower): parsed["sort"] = "price_desc"; query = re.sub(r"\b(expens|high\s*end)\b", "", query, flags=re.IGNORECASE)
        stop_words = {"a", "an", "and", "for", "the", "is", "are", "to", "of", "in", "on", "with", "by", "at", "from", "it", "this", "that", "these", "those"}
        terms = [t for t in re.findall(r"[a-z]{2,}", query.lower()) if t not in stop_words]
        parsed["terms"] = list(dict.fromkeys(terms)); parsed["q"] = " ".join(parsed["terms"])
        return parsed

    def expand_query(self, query: str) -> List[str]:
        synonyms = {"shoe": ["footwear", "sneaker", "boot"], "dress": ["gown", "outfit", "gown"], "phone": ["smartphone", "mobile", "cell"], "laptop": ["computer", "notebook", "pc"], "watch": ["timepiece", "wristwatch"], "headphone": ["headset", "earphone", "earbuds"], "camera": ["photography", "digital camera"], "book": ["novel", "publication", "textbook"], "toy": ["game", "plaything", "childhood"]}
        expanded = [query]; words = query.lower().split()
        for word in words:
            if word in synonyms:
                for syn in synonyms[word]: expanded.append(query.lower().replace(word, syn))
        return list(set(expanded))

    def _apply_text_search(self, db_query, search_term: str):
        if not search_term: return db_query
        like_pattern = f"%{search_term}%"
        if self._is_postgres:
            tsquery = func.plainto_tsquery("english", search_term)
            tsvector = func.to_tsvector("english", Product.name + " " + func.coalesce(Product.description, ""))
            db_query = db_query.filter(or_(tsvector.op("@@")(tsquery), Product.name.ilike(like_pattern), Product.description.ilike(like_pattern), Product.category.ilike(like_pattern), Product.brand.ilike(like_pattern), Product.tags.ilike(like_pattern)))
        else:
            db_query = db_query.filter(or_(Product.name.ilike(like_pattern), Product.description.ilike(like_pattern), Product.category.ilike(like_pattern), Product.brand.ilike(like_pattern), Product.tags.ilike(like_pattern)))
        return db_query

    def search(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 20, offset: int = 0, sort_by: str = "relevance", cursor: Optional[int] = None) -> Dict[str, Any]:
        limit = min(limit, _MAX_PAGE_SIZE); offset = max(offset, 0)
        parsed = self.parse_query(query); all_filters = {**(filters or {}), **parsed}
        db_query = self.db.query(Product).filter(Product.is_deleted == False, Product.is_active == True, Product.is_approved == True, Product.stock > 0)
        if all_filters.get("min_price") is not None: db_query = db_query.filter(Product.price >= float(all_filters["min_price"]))
        if all_filters.get("max_price") is not None: db_query = db_query.filter(Product.price <= float(all_filters["max_price"]))
        if all_filters.get("min_rating") is not None: db_query = db_query.filter(Product.rating >= float(all_filters["min_rating"]))
        if all_filters.get("max_rating") is not None: db_query = db_query.filter(Product.rating <= float(all_filters["max_rating"]))
        if all_filters.get("brands"):
            brands = all_filters["brands"]
            if isinstance(brands, str): brands = [b.strip() for b in brands.split(",") if b.strip()]
            if brands: db_query = db_query.filter(Product.brand.in_(brands))
        if all_filters.get("category"): db_query = db_query.filter(Product.category.ilike(f"%{all_filters['category']}%"))
        if all_filters.get("has_video"): db_query = db_query.filter(Product.video_count > 0)
        db_query = self._apply_text_search(db_query, all_filters.get("q"))
        total = db_query.count()
        if sort_by == "price_asc": db_query = db_query.order_by(Product.price.asc())
        elif sort_by == "price_desc": db_query = db_query.order_by(Product.price.desc())
        elif sort_by == "rating": db_query = db_query.order_by(Product.rating.desc(), Product.sales_count.desc())
        elif sort_by == "newest": db_query = db_query.order_by(Product.created_at.desc())
        else: db_query = db_query.order_by(Product.sales_count.desc(), Product.rating.desc())
        if cursor:
            db_query = db_query.filter(Product.id < cursor)
        products = db_query.order_by(Product.id.desc()).limit(limit).all()
        return {"products": [self._serialize_product(p) for p in products], "total": total, "limit": limit, "offset": offset, "parsed_query": parsed}

    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        return {"id": product.id, "name": product.name, "price": float(product.price) if product.price else 0, "rating": float(product.rating) if product.rating else 0, "brand": product.brand, "category": product.category, "image_url": product.image_url, "stock": product.stock, "video_count": product.video_count or 0}

    def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> List[str]:
        if not query or len(query) < 2: return []
        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms: return []
        last_term = terms[-1].lower(); prefix = f"%{last_term}%"
        name_matches = self.db.query(Product.name).filter(Product.name.ilike(prefix), Product.is_active == True, Product.is_deleted == False).limit(limit * 2).all()
        suggestions = [m[0] for m in name_matches]
        brand_matches = self.db.query(Product.brand).filter(Product.brand.ilike(prefix), Product.brand.isnot(None)).limit(limit * 2).all()
        suggestions.extend([b[0] for b in brand_matches if b[0]])
        if last_term and len(suggestions) > 0:
            fuzzy_matches = get_close_matches(last_term, [s.lower() for s in suggestions if s], n=limit, cutoff=0.6)
            suggestions = [s for s in suggestions if s.lower() in fuzzy_matches or s.lower().startswith(last_term.lower())]
        return list(dict.fromkeys(suggestions))[:limit]

    def fuzzy_search(self, query: str, limit: int = 20, cutoff: float = 0.6) -> Dict[str, Any]:
        limit = min(limit, _MAX_PAGE_SIZE)
        parsed = self.parse_query(query)
        db_query = self.db.query(Product).filter(Product.is_deleted == False, Product.is_active == True, Product.is_approved == True, Product.stock > 0)
        if parsed.get("min_price") is not None: db_query = db_query.filter(Product.price >= float(parsed["min_price"]))
        if parsed.get("max_price") is not None: db_query = db_query.filter(Product.price <= float(parsed["max_price"]))
        if parsed.get("min_rating") is not None: db_query = db_query.filter(Product.rating >= float(parsed["min_rating"]))
        search_term = parsed.get("q")
        if search_term: db_query = self._apply_text_search(db_query, search_term)
        all_products = db_query.limit(_MAX_FUZZY_PRODUCTS).all()
        total = len(all_products)
        query_words = query.lower().split()
        scored_products = []
        for product in all_products:
            product_text = f"{(product.name or '')} {(product.brand or '')} {(product.category or '')}".lower()
            product_words = product_text.split()
            max_word_similarity = 0.0; matched_words = 0
            for qw in query_words:
                word_scores = [SequenceMatcher(None, qw, pw).ratio() for pw in product_words]
                if word_scores:
                    best_score = max(word_scores); max_word_similarity = max(max_word_similarity, best_score)
                    if best_score >= cutoff: matched_words += 1
            overall_similarity = max_word_similarity
            if len(query_words) > 0: overall_similarity = 0.7 * overall_similarity + 0.3 * (matched_words / len(query_words))
            if overall_similarity >= cutoff - 0.1: scored_products.append((overall_similarity, product))
        scored_products.sort(key=lambda x: (-x[0], -(x[1].rating or 0), -(x[1].sales_count or 0)))
        top_products = scored_products[:limit]
        return {"products": [self._serialize_product(p) for s, p in top_products], "total": total, "limit": limit, "offset": 0, "parsed_query": parsed, "fuzzy_applied": cutoff < 1.0, "similarity_scores": [round(s, 2) for s, p in top_products]}


# ── Visual Search Service (merged from visual_search_service.py) ───

def fetch_visually_similar_products(db: Any, limit: int = 10) -> list[dict]:
    """Return a list of candidate products for visual similarity matching."""
    try:
        rows = db.execute(text("SELECT id, name, image_url AS primary_image, COALESCE(price, 0) as price FROM products WHERE is_active = true AND is_approved = true ORDER BY RANDOM() LIMIT :limit"), {"limit": min(limit * 2, 20)}).mappings().all()
        return [{"id": row["id"], "name": row["name"], "image": row["primary_image"], "price": float(row["price"])} for row in rows]
    except Exception as exc:
        logger.warning("Visual search DB query failed: %s", exc)
        return []
def search_products(db: Session, query: str, *, country_code: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Free-text product search across name/description/sku (case-insensitive).

    Returns a lightweight list of product dicts. Degrades to an empty list when
    the query is blank or no matches are found (Law 30).
    """
    from domains.catalog.models.products import Product

    if not query or not query.strip():
        return []
    pattern = f"%{query.strip()}%"
    q = db.query(Product).filter(
        Product.is_deleted == False,
        Product.is_active == True,
        (Product.name.ilike(pattern) | Product.description.ilike(pattern) | Product.sku.ilike(pattern)),
    )
    if country_code:
        q = q.filter(Product.country_code == country_code)
    rows = q.order_by(Product.created_at.desc()).limit(limit).offset(offset).all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "price": float(p.price) if p.price is not None else None,
            "image_url": p.image_url,
            "country_code": p.country_code,
        }
        for p in rows
    ]

def load_search_catalog(products: list[dict]) -> int:
    """Index a batch of products into the search catalog.

    Degrades gracefully (Law 30): returns the count accepted without raising when
    the search backend is unavailable.
    """
    try:
        for p in products:
            _SEARCH_INDEX.setdefault(p.get("country_code", "_all"), {})[str(p.get("id"))] = p
        return len(products)
    except Exception:
        return 0
