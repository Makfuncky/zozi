"""Search Service â€” natural-language query parsing and smart product search logic.

Service layer for search functionality to avoid controller imports in other controllers.
"""
import hashlib
import json
import re
from typing import Any, Optional, List, cast

from fastapi.responses import Response
from sqlalchemy import desc, func, or_
from sqlalchemy.orm import Session

from models.catalog.products import Product
from data.schemas import _normalize_image_path
from utils.cache import cache_or_compute


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

PRICE_KEYWORDS: list[tuple[re.Pattern, float | None, float | None]] = [
    (re.compile(r"\bcheap\b|\bbudget\b|\baffordable\b", re.I), None, 50.0),
    (re.compile(r"\bmid[- ]?range\b|\bmoderate\b", re.I), 50.0, 200.0),
    (re.compile(r"\bpremium\b|\bluxury\b|\bexpensive\b|\bhigh[- ]?end\b", re.I), 200.0, None),
]

BETWEEN_PAT = re.compile(r"\bbetween\s+(\d+(?:\.\d+)?)\s+(?:and|to|-)\s+(\d+(?:\.\d+)?)\b", re.I)
UNDER_PAT = re.compile(r"\bunder\s+(\d+(?:\.\d+)?)\b", re.I)
ABOVE_PAT = re.compile(r"\bover\s+(\d+(?:\.\d+)?)\b|\babove\s+(\d+(?:\.\d+)?)", re.I)
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
    (re.compile(r"\b(good\s+quality|high\s+quality|best\s+quality|durable|premium\s+quality)\b", re.I), None, "quality"),
]

TEXT_SEARCH_FIELDS = (
    Product.name,
    Product.description,
    Product.category,
    Product.brand,
    Product.tags,
    Product.ai_description,
    Product.materials,
)


def _normalize_query_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


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

    m_between = BETWEEN_PAT.search(q)
    m_under = UNDER_PAT.search(q)
    m_above = ABOVE_PAT.search(q)

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

    min_rating, quality_sort, quality = None, None, None
    for pattern, mr, qs, q in QUALITY_PATTERNS:
        if pattern.search(q):
            min_rating, quality_sort, quality = mr, qs, q
            break
    result["min_rating"] = min_rating
    result["quality"] = quality

    q_lower = q.lower()
    for category, keywords in CATEGORY_SYNONYMS.items():
        if any(kw in q_lower for kw in keywords):
            result["category"] = category
            break

    text_match = TEXT_SIZE_VALUE_PAT.search(q)
    if text_match:
        normalized = re.sub(r"\s+", " ", text_match.group(1).strip().lower())
        result["size"] = SIZE_NORMALIZATION.get(normalized, text_match.group(1).strip().upper())

    numeric_match = NUMERIC_SIZE_VALUE_PAT.search(q)
    if numeric_match and not text_match:
        normalized = re.sub(r"\s+", " ", numeric_match.group(1).strip().lower())
        result["size"] = SIZE_NORMALIZATION.get(normalized, numeric_match.group(1).strip().upper())

    color_match = None
    for alias in COLOR_ALIASES:
        if re.search(rf"\b{re.escape(alias)}\b", q_lower):
            color_match = COLOR_ALIASES[alias]
            break
    if color_match:
        result["color"] = color_match

    if re.search(r"\bbest\b|\btop[- ]?rated\b|\bhighest\s+rating\b", q, re.I):
        result["sort"] = "rating"
    elif re.search(r"\bnewest\b|\blatest\b|\bnew\b", q, re.I):
        result["sort"] = "newest"
    elif re.search(r"\bcheapest\b|\blowest\s+price\b", q, re.I):
        result["sort"] = "price_asc"
    elif quality_sort:
        result["sort"] = quality_sort

    clean_q = BETWEEN_PAT.sub("", q)
    clean_q = UNDER_PAT.sub("", clean_q)
    clean_q = ABOVE_PAT.sub("", clean_q)
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
        clean_q = re.sub(rf"\b(?:size\s+)?{re.escape(result['size'])}\b", " ", clean_q, flags=re.I)
    for pattern, _min_rating, _sort, _quality in QUALITY_PATTERNS:
        clean_q = pattern.sub(" ", clean_q)
    clean_q = _normalize_query_text(clean_q.replace("-", " "))
    result["q"] = clean_q or q
    result["terms"] = _extract_terms(clean_q or q)
    return result


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


def smart_search(q: str, limit: int, db: Session, response: Optional[Response] = None, supplier_id: Optional[int] = None) -> dict:
    parsed = parse_query(q)
    return smart_search_from_parsed(
        parsed=parsed,
        limit=limit,
        db=db,
        response=response,
        supplier_id=supplier_id,
    )


def smart_search_from_parsed(
    parsed: dict,
    limit: int,
    db: Session,
    response: Optional[Response] = None,
    shopper_profile: Optional[dict[str, Any]] = None,
    supplier_id: Optional[int] = None,
) -> dict:
    from sqlalchemy import or_

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

    if parsed.get("brand"):
        brand_cache_key = f"search:brand_catalog:{hashlib.sha1(parsed['raw_q'].encode()).hexdigest()}" 
        def _fetch_brands():
            brand_rows = (
                db.query(Product.brand)
                .filter(
                    Product.is_deleted == False,
                    Product.is_active == True,
                    Product.is_approved == True,
                    Product.stock > 0,
                    Product.brand.isnot(None),
                )
                .distinct()
                .all()
            )
            return sorted([cast(str, row[0]).strip() for row in brand_rows if row and row[0]], key=len, reverse=True)
        brands = cache_or_compute(key=brand_cache_key, compute=_fetch_brands, ttl=300, namespace="products:search")
        for brand in brands:
            if re.search(rf"\b{re.escape(brand.lower())}\b", parsed["raw_q"].lower()):
                updated = dict(parsed)
                updated["brand"] = brand
                updated["q"] = parsed["q"]
                return smart_search_from_parsed(updated, limit, db, response, shopper_profile, supplier_id)

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
    def _database_supports_postgres_fts(db: Session) -> bool:
        bind = db.get_bind()
        return bool(bind is not None and bind.dialect.name == "postgresql")

    if _database_supports_postgres_fts(db):
        def _build_postgres_tsquery(p: dict):
            phrases: list[str] = []
            cleaned_query = _normalize_query_text(str(p.get("q") or ""))
            if cleaned_query:
                phrases.append(cleaned_query)
            if p.get("brand"):
                phrases.append(str(p["brand"]))
            if p.get("color"):
                phrases.append(str(p["color"]))
            if p.get("size"):
                phrases.append(str(p["size"]))
            query_text = " ".join(dict.fromkeys(phrases)).strip()
            if not query_text:
                return None
            return func.websearch_to_tsquery("simple", query_text)
        ts_query = _build_postgres_tsquery(parsed)
        if ts_query is not None:
            search_document = Product.search_vector
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

    normalized_products = [
        {
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "rating": p.rating,
            "brand": getattr(p, "brand", None),
            "image_url": _normalize_image_path(getattr(p, "image_url")),
            "category": p.category,
            "stock": p.stock,
            "color": getattr(p, "color", None),
            "sizes": _deserialize_sizes(getattr(p, "sizes", None)),
        }
        for p in candidates
    ]

    if response is not None:
        response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=60"

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
        "products": normalized_products,
        "results": normalized_products,
    }

def fetch_brands_for_search(db: Session) -> list[str]:
    """Fetch distinct product brands for search autocomplete — delegated from controller."""
    brand_rows = (
        db.query(Product.brand)
        .filter(
            Product.is_deleted == False,  # noqa: E712
            Product.is_active == True,    # noqa: E712
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


def compute_category_weights(db: Session, user_id: int, normalized_recent_categories: list[str]) -> tuple[dict, Optional[float], Optional[float], set]:
    """Compute weighted categories from purchase history — delegated from controller."""
    from sqlalchemy import func
    from catalog.models import Order, OrderItem, Wishlist, Product as ProdModel
    
    category_rows = (
        db.query(Product.category, func.sum(OrderItem.quantity).label("units"))
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
            ProdModel.is_approved == True,  # noqa: E712
        )
        .group_by(Product.category)
        .order_by(desc(func.sum(OrderItem.quantity)))
        .all()
    )
    weighted_categories: dict[str, float] = {
        (row.category or "Uncategorized"): float(row.units or 0)
        for row in category_rows
    }

    wishlist_rows = (
        db.query(Product.category)
        .join(Wishlist, Wishlist.product_id == ProdModel.id)
        .filter(
            Wishlist.user_id == user_id,
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
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
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
        .filter(
            OrderItem.order_id.in_(co_order_ids_subq),
            ProdModel.id.notin_(user_product_ids_subq),
            ProdModel.is_deleted == False,  # noqa: E712
            ProdModel.is_active == True,    # noqa: E712
            ProdModel.is_approved == True,  # noqa: E712
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

    price_avg_row = (
        db.query(func.avg(Product.price).label("avg_price"))
        .join(OrderItem, OrderItem.product_id == ProdModel.id)
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

    purchased_product_ids = {
        row.product_id
        for row in db.query(OrderItem.product_id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .distinct()
        .all()
    }

    top_categories = [
        category
        for category, _score in sorted(
            weighted_categories.items(),
            key=lambda kv: kv[1],
            reverse=True,
        )[:4]
    ]

    return weighted_categories, price_band_lo, price_band_hi, purchased_product_ids
