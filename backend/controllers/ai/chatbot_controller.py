"""
Chatbot Controller — conversational assistant for ZOZI customers.

Handles:
  - Product search intent → search DB
  - FAQ intents (orders, shipping, returns, payments) → static answers
  - Context-aware follow-up messages
  - AI-powered response escalation when HuggingFace token is present
  - In-memory per-session conversation history (last 10 messages)
"""
from collections import Counter
import json
import logging
import re
import time
from typing import Any, Optional, cast

from sqlalchemy import func
from sqlalchemy.orm import Session

import controllers.search_controller as search_ctrl
from data.models import ChatbotQueryEvent, Order, OrderItem, Product, User, Wishlist
from data.services_write_helpers import (
from services.ai.ai_service import get_user_by_id
    add_and_flush,
    commit_only,
)

logger = logging.getLogger(__name__)

# ─── In-memory session history ────────────────────────────────────────────────
# {session_id: {"messages": [{"role": "user"|"bot", "text": str}], "last_active": float}}
_SESSION_HISTORY: dict[str, dict] = {}
_SESSION_TTL = 24 * 3600  # 24 hours idle TTL
_SESSION_MAX_MESSAGES = 10  # keep last N turns


def _get_or_create_session(session_id: Optional[str]) -> tuple[str, list[dict]]:
    """Return (session_id, history_list). Creates new session if needed; prunes stale ones."""
    import uuid
    now = time.monotonic()

    # Prune stale sessions (cheap — only checked on each call)
    stale = [sid for sid, s in _SESSION_HISTORY.items() if now - s["last_active"] > _SESSION_TTL]
    for sid in stale:
        _SESSION_HISTORY.pop(sid, None)

    sid = session_id or str(uuid.uuid4())
    if sid not in _SESSION_HISTORY:
        _SESSION_HISTORY[sid] = {"messages": [], "last_active": now}
    else:
        _SESSION_HISTORY[sid]["last_active"] = now

    return sid, _SESSION_HISTORY[sid]["messages"]


def _append_to_session(session_id: str, role: str, text: str) -> None:
    if session_id not in _SESSION_HISTORY:
        return
    msgs = _SESSION_HISTORY[session_id]["messages"]
    msgs.append({"role": role, "text": text})
    # Keep only the last N messages
    _SESSION_HISTORY[session_id]["messages"] = msgs[-_SESSION_MAX_MESSAGES:]

# ─── Intent patterns (ordered by priority) ───────────────────────────────────
_INTENT_PATTERNS = [
    ("product_search", re.compile(
        r"\b(find|show|search|looking for|recommend|suggest|any|cheapest?|best|top|latest|"
        r"new|cheap|budget|affordable|premium|quality|under|over|between|got|have|sell|buy|get)\b",
        re.IGNORECASE,
    )),
    ("order_status", re.compile(r"\bmy order|order status|track\b", re.IGNORECASE)),
    ("shipping", re.compile(r"\bship|deliver|dispatch|arrive|how long\b", re.IGNORECASE)),
    ("return", re.compile(r"\breturn|refund|exchange|broken|damaged|wrong\b", re.IGNORECASE)),
    ("payment", re.compile(r"\bpay|card|stripe|tap|price|cost|amount|checkout\b", re.IGNORECASE)),
    ("account", re.compile(r"\baccount|profile|password|login|sign in|register\b", re.IGNORECASE)),
    ("help", re.compile(r"\bhelp|support|contact|assist\b", re.IGNORECASE)),
    ("greeting", re.compile(r"^(hi|hello|hey|salaam|مرحبا|السلام عليكم)\b", re.IGNORECASE)),
]

_NOISE_IN_PRODUCT = re.compile(
    r"\b(order|ship|return|refund|pay|support|help|account|password)\b",
    re.IGNORECASE,
)

_SEARCH_STOPWORDS = {
    "find", "show", "search", "looking", "look", "for", "recommend", "suggest",
    "any", "best", "top", "latest", "new", "under", "over", "between", "with",
    "that", "this", "from", "have", "sell", "buy", "get", "cheap", "price",
}
_PRODUCT_REQUEST_HINT = re.compile(
    r"\b(find|show|search|looking for|recommend|suggest|cheap|budget|affordable|premium|quality|"
    r"under|over|between|options?|products?|items?)\b",
    re.IGNORECASE,
)
_PRODUCT_REFERENCE_HINT = re.compile(
    r"\b(one|ones|those|these|them|another|more|similar|options?)\b",
    re.IGNORECASE,
)


def _classify_intent(message: str) -> str:
    for intent, pattern in _INTENT_PATTERNS:
        if pattern.search(message):
            if intent == "product_search" and _NOISE_IN_PRODUCT.search(message):
                continue
            return intent
    return "unknown"


# ─── Static FAQ answers ───────────────────────────────────────────────────────
_STATIC_REPLIES = {
    "greeting": "Hi, I’m your ZOZI shopping assistant. I can help you find strong matches, compare styles, and narrow the catalog by budget, color, size, or quality. Try something like 'show me black fashion under 300', 'laptops under 1000', or 'show me top-rated t-shirt options'.",
    "order_status": "To check your order status, go to **My Orders** in your profile. If you need further help, please share your order number and our support team will assist you.",
    "shipping": "We deliver across the GCC region. Standard delivery takes **3–7 business days**. Express options may be available at checkout. Free shipping on orders above AED 200.",
    "return": "Our return policy allows returns within **14 days** of delivery. Items must be unused and in original packaging. Visit **My Orders → Request Return** to start the process.",
    "payment": "We accept all major credit/debit cards, Apple Pay, and local payment methods via Stripe and Tap Payments. All transactions are secured with 256-bit encryption.",
    "account": "You can manage your account, addresses, and preferences in the **Profile** section. Forgot your password? Use **Forgot Password** on the login page.",
    "help": "I can help you shop more efficiently: find products, compare options, explain shipping or returns, and narrow choices by budget, brand, size, or rating. Try prompts like 'show me black fashion under 300', 'best-rated headphones', or 'more affordable options'.",
    "unknown": "I can help with shopping, shipping, returns, and checkout. If you’re looking for a product, try adding a few details like type, color, budget, brand, or quality level.",
}

_STATIC_REPLIES_AR = {
    "greeting": "مرحبًا، أنا مساعد التسوق الخاص بك في زوزي. أستطيع مساعدتك في إيجاد أفضل المنتجات ومقارنة الأنماط وتضييق البحث حسب الميزانية أو اللون أو المقاس أو الجودة. جرّب مثلاً 'اعرض أزياء سوداء تحت 300' أو 'لابتوبات تحت 1000'.",
    "order_status": "لمتابعة حالة طلبك، توجه إلى **طلباتي** في ملفك الشخصي. إذا كنت بحاجة إلى مزيد من المساعدة، شارك رقم الطلب وسيتواصل فريق الدعم معك.",
    "shipping": "نوصّل في جميع أنحاء منطقة الخليج. التوصيل القياسي يستغرق **3–7 أيام عمل**. قد تتوفر خيارات سريعة عند الدفع. شحن مجاني للطلبات فوق 200 درهم.",
    "return": "تسمح سياستنا بإرجاع المنتجات خلال **14 يومًا** من التسليم. يجب أن تكون العناصر غير مستخدمة وفي تغليفها الأصلي. توجه إلى **طلباتي ← طلب إرجاع** لبدء العملية.",
    "payment": "نقبل جميع بطاقات الائتمان/الخصم الرئيسية، وأبل باي، وطرق الدفع المحلية عبر Stripe وTap Payments. جميع المعاملات محمية بتشفير 256-bit.",
    "account": "يمكنك إدارة حسابك وعناوينك وتفضيلاتك من قسم **الملف الشخصي**. نسيت كلمة المرور؟ استخدم **نسيت كلمة المرور** في صفحة الدخول.",
    "help": "يمكنني مساعدتك في التسوق بفعالية: إيجاد المنتجات، مقارنة الخيارات، شرح الشحن والإرجاع، وتضييق الخيارات حسب الميزانية أو العلامة أو المقاس أو التقييم. جرّب 'اعرض أزياء سوداء تحت 300' أو 'أفضل السماعات تقييمًا'.",
    "unknown": "يمكنني مساعدتك في التسوق والشحن والإرجاع والدفع. إذا كنت تبحث عن منتج، أضف بعض التفاصيل مثل النوع أو اللون أو الميزانية أو العلامة أو مستوى الجودة.",
}


def _static_reply(intent: str, lang: str = "en") -> str:
    source = _STATIC_REPLIES_AR if lang == "ar" else _STATIC_REPLIES
    fallback = _STATIC_REPLIES_AR.get(intent) if lang == "ar" else _STATIC_REPLIES.get(intent)
    return source.get(intent, fallback or _STATIC_REPLIES["unknown"])


# ─── Product search ───────────────────────────────────────────────────────────
def _extract_search_keywords(message: str) -> str:
    """Strip intent words and return the product search query."""
    noise = re.compile(
        r"\b(find|show|search|looking for|do you|you have|sell|buy|get|any|got|"
        r"recommend|suggest|cheapest?|best|top|latest|new|under|over|between)\b",
        re.IGNORECASE,
    )
    cleaned = noise.sub("", message).strip(" ?.,!")
    # Remove price constraints — keep for later
    cleaned = re.sub(r"\b(AED|OMR|USD)?\s*\d+(\s*-\s*\d+)?\b", "", cleaned).strip()
    return cleaned or message.strip()


def _extract_max_price(message: str) -> Optional[float]:
    match = re.search(r"under\s+(AED|OMR|USD)?\s*(\d+(?:\.\d+)?)", message, re.IGNORECASE)
    if match:
        return float(match.group(2))
    return None


def _search_tokens(message: str) -> list[str]:
    keywords = _extract_search_keywords(message)
    return [
        token
        for token in re.findall(r"[a-zA-Z0-9]+", keywords.lower())
        if len(token) > 2 and token not in _SEARCH_STOPWORDS
    ]


def _serialize_products(products: list[Product]) -> list[dict]:
    return [
        {
            "id": p.id,
            "name": p.name,
            "price": float(cast(Any, getattr(p, "price")) or 0),
            "rating": round(float(cast(Any, getattr(p, "rating")) or 0), 1),
            "image_url": p.image_url,
            "category": p.category,
            "stock": p.stock,
        }
        for p in products
    ]


def _catalog_guidance_reply(db: Session, message: str, supplier_id: Optional[int] = None, lang: str = "en") -> str:
    top_products_query = _db_product_query_0(db, is_, is_deleted)


    categories_query = db.query(Product.category).filter(
        Product.is_deleted.is_(False),
        Product.is_active.is_(True),
        Product.is_approved.is_(True),
        Product.stock > 0,
        Product.category.isnot(None),
    )

    if supplier_id is not None:
        top_products_query = top_products_query.filter(Product.supplier_id == supplier_id)
        categories_query = categories_query.filter(Product.supplier_id == supplier_id)

    top_products = top_products_query.order_by(Product.sales_count.desc()).limit(3).all()
    category_rows = categories_query.distinct().limit(4).all()
    categories = [row[0] for row in category_rows if row and row[0]]
    category_text = ", ".join(categories) if categories else ("كتالوجنا" if lang == "ar" else "our catalog")
    product_text = ", ".join(cast(str, product.name) for product in top_products) if top_products else ("الأكثر مبيعًا" if lang == "ar" else "our best sellers")
    cleaned = _extract_search_keywords(message)
    if lang == "ar":
        return (
            f"لم أتمكن من إيجاد تطابق دقيق لـ '{cleaned}'، لكن لا يزال بإمكاني المساعدة. "
            f"جرّب اسمًا أوسع للمنتج أو علامة تجارية أو نطاق سعر مثل 'أحذية رياضية تحت 300'. "
            f"يمكنك أيضًا تصفح فئات مثل {category_text}، أو البدء بمنتجات رائجة مثل {product_text}."
        )
    return (
        f"I couldn't find an exact match for '{cleaned}', but I can still help. "
        f"Try a broader product name, a brand, or a price range like 'running shoes under 300'. "
        f"You can also browse categories such as {category_text}, or start with popular items like {product_text}."
    )


def search_products(db: Session, message: str, limit: int = 5) -> list[dict]:
    """Shared smart search wrapper for chatbot context."""
    return cast(list[dict], search_ctrl.smart_search(q=message, limit=limit, db=db).get("products", []))


def search_products_with_context(
    db: Session,
    parsed_filters: dict[str, Any],
    limit: int = 5,
    user_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
) -> dict[str, Any]:
    shopper_profile = get_shopper_profile(db, user_id)
    result = cast(
        dict[str, Any],
        search_ctrl.smart_search_from_parsed(
            parsed=parsed_filters,
            limit=limit,
            db=db,
            shopper_profile=shopper_profile,
            supplier_id=supplier_id,
        ),
    )
    if shopper_profile:
        result["shopper_profile"] = shopper_profile
    return result


def _format_price_value(value: Optional[float]) -> str:
    if value is None:
        return ""
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _safe_json_dumps(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=True, default=str)


def _load_browsing_history(user: User) -> list[int]:
    browsing_history_json = cast(str | None, getattr(user, "browsing_history_json"))
    if not browsing_history_json:
        return []
    try:
        loaded = json.loads(browsing_history_json)
        if isinstance(loaded, list):
            return [int(item) for item in loaded if str(item).isdigit()]
    except (TypeError, ValueError, json.JSONDecodeError):
        return []
    return []


def _top_counter_values(counter: Counter[str], limit: int = 3) -> list[str]:
    return [item for item, _score in counter.most_common(limit) if item]


def get_shopper_profile(db: Session, user_id: Optional[int]) -> dict[str, Any]:
    if not user_id:
        return {}

    category_scores: Counter[str] = Counter()
    brand_scores: Counter[str] = Counter()
    size_scores: Counter[str] = Counter()

    purchased_rows = (
        db.query(
            Product.category,
            Product.brand,
            OrderItem.selected_size,
            func.sum(OrderItem.quantity).label("units"),
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(
            Order.user_id == user_id,
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
            Product.is_approved.is_(True),
        )
        .group_by(Product.category, Product.brand, OrderItem.selected_size)
        .all()
    )
    for row in purchased_rows:
        weight = int(row.units or 0) * 3
        if row.category:
            category_scores[str(row.category)] += weight
        if row.brand:
            brand_scores[str(row.brand)] += weight
        if row.selected_size:
            size_scores[str(row.selected_size).upper()] += weight

    wishlist_rows = (
        db.query(Product.category, Product.brand)
        .join(Wishlist, Wishlist.product_id == Product.id)
        .filter(
            Wishlist.user_id == user_id,
            Product.is_deleted.is_(False),
            Product.is_active.is_(True),
            Product.is_approved.is_(True),
        )
        .all()
    )
    for category, brand in wishlist_rows:
        if category:
            category_scores[str(category)] += 2
        if brand:
            brand_scores[str(brand)] += 2

    user = get_user_by_id(db, user_id)
    browsing_history = _load_browsing_history(user) if user else []
    if browsing_history:
        viewed_rows = (
            db.query(Product.category, Product.brand)
            .filter(Product.id.in_(browsing_history[:20]))
            .all()
        )
        for category, brand in viewed_rows:
            if category:
                category_scores[str(category)] += 1
            if brand:
                brand_scores[str(brand)] += 1

    avg_spend = (
        db.query(func.avg(OrderItem.price))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user_id)
        .scalar()
    )

    return {
        "preferred_categories": _top_counter_values(category_scores),
        "preferred_brands": _top_counter_values(brand_scores),
        "preferred_sizes": _top_counter_values(size_scores),
        "preferred_price": float(avg_spend or 0) if avg_spend is not None else None,
        "has_history": bool(category_scores or brand_scores or size_scores or avg_spend),
    }


def _record_chatbot_event(
    db: Session,
    *,
    session_id: str,
    event_type: str,
    user_id: Optional[int] = None,
    message: Optional[str] = None,
    normalized_query: Optional[str] = None,
    intent: Optional[str] = None,
    filters: Optional[dict[str, Any]] = None,
    result_count: int = 0,
    product_ids: Optional[list[int]] = None,
    clicked_product_id: Optional[int] = None,
) -> None:
    event = ChatbotQueryEvent(
        user_id=user_id,
        session_id=session_id,
        event_type=event_type,
        message=message,
        normalized_query=(normalized_query or None),
        intent=intent,
        filters_json=_safe_json_dumps(filters) if filters else None,
        result_count=max(result_count, 0),
        product_ids_json=_safe_json_dumps(product_ids) if product_ids else None,
        clicked_product_id=clicked_product_id,
    )
    add_and_flush(db, event)
    commit_only(db)


def _profile_personalization_hint(shopper_profile: dict[str, Any], parsed_filters: dict[str, Any]) -> str:
    if not shopper_profile or not shopper_profile.get("has_history"):
        return ""
    if parsed_filters.get("brand"):
        return ""
    preferred_brands = cast(list[str], shopper_profile.get("preferred_brands") or [])
    preferred_categories = cast(list[str], shopper_profile.get("preferred_categories") or [])
    if preferred_brands:
        return f" I prioritised options close to your usual {preferred_brands[0]} preferences."
    if preferred_categories:
        return f" I prioritised options close to your usual {preferred_categories[0]} shopping habits."
    return ""


def _upsell_hint(products: list[dict[str, Any]], lang: str = "en") -> str:
    if not products:
        return ""
    lead_category = str(products[0].get("category") or "").lower()
    if "elect" in lead_category:
        return " يمكنني أيضًا عرض ملحقات مطابقة مثل الشواحن والحافظات والمكبرات الصوتية." if lang == "ar" else " I can also show matching accessories like chargers, cases, or speakers."
    if "fashion" in lead_category or "cloth" in lead_category or "shirt" in lead_category:
        return " يمكنني أيضًا مساعدتك في تنسيق هذا مع المقاسات والألوان أو قطع أزياء متناسقة." if lang == "ar" else " I can also help you match this with sizes, colors, or complementary fashion items."
    if "home" in lead_category:
        return " يمكنني أيضًا عرض قطع منزلية متناسقة أو بدائل مناسبة للشراء المجمّع." if lang == "ar" else " I can also surface matching home pieces or bundle-friendly alternatives."
    return ""


def _price_badge(product: dict[str, Any]) -> str:
    value = cast(Optional[float], product.get("price"))
    if value in (None, 0):
        return ""
    return f"AED {_format_price_value(float(value))}"


def _lead_product_line(product: dict[str, Any]) -> str:
    parts = [str(product.get("name") or "This item")]
    price_badge = _price_badge(product)
    rating = cast(Optional[float], product.get("rating"))
    if price_badge:
        parts.append(price_badge)
    if rating:
        parts.append(f"rated {float(rating):.1f}")
    return ", ".join(parts)


def _result_guidance_line(parsed_filters: dict[str, Any], products: list[dict[str, Any]], lang: str = "en") -> str:
    cues: list[str] = []
    if not parsed_filters.get("size"):
        cues.append("size")
    if not parsed_filters.get("max_price") and not parsed_filters.get("min_price"):
        cues.append("budget")
    if not parsed_filters.get("brand"):
        cues.append("brand")
    if parsed_filters.get("sort") != "rating":
        cues.append("best-rated")

    if lang == "ar":
        ar_cues = {"size": "المقاس", "budget": "الميزانية", "brand": "العلامة التجارية", "best-rated": "الأعلى تقييمًا"}
        if cues:
            labeled = [ar_cues.get(c, c) for c in cues]
            if len(cues) == 1:
                return f"إذا رغبت، يمكنني تضييق النتائج حسب {labeled[0]}."
            return f"إذا رغبت، يمكنني تضييق النتائج حسب {', '.join(labeled[:-1])}، أو {labeled[-1]}."
        lead_category = str(products[0].get("category") or "").strip().lower() if products else ""
        if lead_category:
            return f"إذا رغبت، يمكنني استكشاف المزيد من خيارات {lead_category} المشابهة."
        return "إذا رغبت، يمكنني مواصلة تضييق هذه الخيارات لك."

    if cues:
        if len(cues) == 1:
            return f"If you want, I can narrow this down by {cues[0]}."
        return f"If you want, I can narrow this down by {', '.join(cues[:-1])}, or {cues[-1]}."

    lead_category = str(products[0].get("category") or "").strip().lower() if products else ""
    if lead_category:
        return f"If you want, I can keep exploring similar {lead_category} options."
    return "If you want, I can keep narrowing these options for you."


def _style_reference_terms(parsed_filters: dict[str, Any]) -> set[str]:
    reference_terms = set(cast(list[str], parsed_filters.get("terms") or []))
    for key in ("q", "raw_q"):
        reference_terms.update(search_ctrl._extract_terms(str(parsed_filters.get(key) or "")))

    requested_color = cast(Optional[str], parsed_filters.get("color"))
    requested_brand = cast(Optional[str], parsed_filters.get("brand"))
    requested_category = cast(Optional[str], parsed_filters.get("category"))

    for value in (requested_color, requested_brand, requested_category):
        if value:
            reference_terms.update(search_ctrl._extract_terms(value))

    return {term for term in reference_terms if term}


def _price_proximity_score(price: Optional[float], parsed_filters: dict[str, Any], shopper_profile: Optional[dict[str, Any]]) -> float:
    if price in (None, 0):
        return 0.0

    numeric_price = float(price)
    max_price = cast(Optional[float], parsed_filters.get("max_price"))
    min_price = cast(Optional[float], parsed_filters.get("min_price"))
    preferred_price = cast(Optional[float], (shopper_profile or {}).get("preferred_price"))

    if max_price:
        gap = max(max_price - numeric_price, 0.0)
        return max(0.0, 2.5 - gap / max(max_price, 1.0))
    if min_price:
        gap = max(numeric_price - min_price, 0.0)
        return max(0.0, 1.8 - gap / max(min_price, 1.0))
    if preferred_price:
        return max(0.0, 1.5 - abs(numeric_price - preferred_price) / max(preferred_price, 1.0))
    return 0.0


def _style_similarity_score(
    product: dict[str, Any],
    parsed_filters: dict[str, Any],
    shopper_profile: Optional[dict[str, Any]] = None,
) -> float:
    requested_color = str(parsed_filters.get("color") or "").strip().lower()
    requested_brand = str(parsed_filters.get("brand") or "").strip().lower()
    requested_category = str(parsed_filters.get("category") or "").strip().lower()
    requested_size = str(parsed_filters.get("size") or "").strip().lower()
    product_name = str(product.get("name") or "").lower()
    product_brand = str(product.get("brand") or "").strip().lower()
    product_category = str(product.get("category") or "").strip().lower()
    product_color = str(product.get("color") or "").strip().lower()
    product_sizes = {str(size).strip().lower() for size in cast(list[str], product.get("sizes") or [])}
    product_terms = set(re.findall(r"[a-z0-9]+", " ".join(filter(None, [product_name, product_brand, product_category, product_color]))))
    reference_terms = _style_reference_terms(parsed_filters)
    overlap = reference_terms & product_terms
    fuzzy_overlap = sum(
        1
        for term in reference_terms
        if any(
            candidate.startswith(term) or term.startswith(candidate)
            for candidate in product_terms
            if candidate != term
        )
    )
    score = float(len(overlap)) * 2.4
    score += float(fuzzy_overlap) * 2.1

    if requested_category:
        if requested_category == product_category:
            score += 7.0
        elif requested_category in product_category or product_category in requested_category:
            score += 4.0

    if requested_color:
        if requested_color == product_color:
            score += 5.0
        elif requested_color in product_name:
            score += 2.2

    if requested_brand:
        if requested_brand == product_brand:
            score += 4.5
        elif requested_brand in product_name:
            score += 1.8

    if requested_size and requested_size in product_sizes:
        score += 1.5

    preferred_categories = {str(value).lower() for value in cast(list[str], (shopper_profile or {}).get("preferred_categories") or [])}
    preferred_brands = {str(value).lower() for value in cast(list[str], (shopper_profile or {}).get("preferred_brands") or [])}
    if product_category and product_category in preferred_categories:
        score += 1.2
    if product_brand and product_brand in preferred_brands:
        score += 1.0

    score += float(cast(Optional[float], product.get("rating")) or 0)
    score += _price_proximity_score(cast(Optional[float], product.get("price")), parsed_filters, shopper_profile)
    return score


def _category_sales_line(parsed_filters: dict[str, Any], products: list[dict[str, Any]], result_mode: str, lang: str = "en") -> str:
    lead_category = str((products[0].get("category") if products else None) or parsed_filters.get("category") or "").strip().lower()
    if not lead_category:
        return ""

    AR = {
        "fashion_close": " these الخيارات القريبة من الأزياء تحافظ على نفس الألوان والمظهر والإطلالة اليومية.",
        "fashion": " ركّزت على قطع بستايل عملي وتنسيق ألوان قوي وسهلة التنسيق.",
        "tech_close": " these الخيارات التقنية القريبة تحافظ على نفس الاستخدام والمزايا ونطاق القيمة الذي طلبته.",
        "tech": " ركّزت على مواصفات موثوقة وتقييمات قوية وأداء يومي جيد القيمة.",
        "beauty_close": " these الخيارات التجميلية القريبة تحافظ على نفس الروتين واللمسة والعناية الذاتية.",
        "beauty": " ركّزت على جودة التركيبة واللمسة وقيمة العنا الذاتية لتسهّل التسوّق.",
    }
    if "fashion" in lead_category or "cloth" in lead_category:
        if result_mode == "close":
            return AR["fashion_close"] if lang == "ar" else " These close fashion picks stay near the same color story, silhouette, and everyday styling vibe."
        return AR["fashion"] if lang == "ar" else " I leaned toward pieces with wearable styling, strong color coordination, and easy outfit pairing."

    if "elect" in lead_category or "tech" in lead_category:
        if result_mode == "close":
            return AR["tech_close"] if lang == "ar" else " These close tech picks stay near the use case, feature mix, and value range you asked for."
        return AR["tech"] if lang == "ar" else " I leaned toward dependable specs, solid ratings, and everyday performance value."

    if "beauty" in lead_category or "cosmetic" in lead_category or "skin" in lead_category:
        if result_mode == "close":
            return AR["beauty_close"] if lang == "ar" else " These close beauty picks stay near the same routine, finish, and self-care focus."
        return AR["beauty"] if lang == "ar" else " I focused on formula quality, finish, and self-care value so the shortlist feels easy to shop."

    return ""


def _build_relaxed_product_recommendations(
    db: Session,
    parsed_filters: dict[str, Any],
    shopper_profile: Optional[dict[str, Any]] = None,
    limit: int = 4,
    supplier_id: Optional[int] = None,
) -> list[dict[str, Any]]:
    base = {
        "raw_q": parsed_filters.get("raw_q") or parsed_filters.get("q") or "",
        "q": "",
        "terms": [],
        "min_price": parsed_filters.get("min_price"),
        "max_price": parsed_filters.get("max_price"),
        "category": parsed_filters.get("category"),
        "brand": parsed_filters.get("brand"),
        "size": parsed_filters.get("size"),
        "color": parsed_filters.get("color"),
        "min_rating": parsed_filters.get("min_rating"),
        "quality": parsed_filters.get("quality"),
        "sort": parsed_filters.get("sort") or "rating",
    }

    variants: list[dict[str, Any]] = [dict(base)]
    if base.get("size"):
        variant = dict(base)
        variant["size"] = None
        variants.append(variant)
    if base.get("brand"):
        variant = dict(base)
        variant["brand"] = None
        variant["size"] = None
        variants.append(variant)
    if base.get("category") and base.get("color"):
        variant = dict(base)
        variant["brand"] = None
        variant["size"] = None
        variants.append(variant)
    if base.get("category"):
        variant = dict(base)
        variant["brand"] = None
        variant["color"] = None
        variant["size"] = None
        variants.append(variant)
    if base.get("color"):
        variant = dict(base)
        variant["brand"] = None
        variant["category"] = None
        variant["size"] = None
        variants.append(variant)

    preferred_categories = cast(list[str], (shopper_profile or {}).get("preferred_categories") or [])
    if preferred_categories and not base.get("category"):
        variant = dict(base)
        variant["category"] = preferred_categories[0]
        variant["brand"] = None
        variant["color"] = None if not base.get("color") else base.get("color")
        variant["size"] = None
        variants.append(variant)

    collected: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    seen_variants: set[str] = set()
    candidate_limit = max(limit * 3, 6)

    for variant in variants:
        signature = json.dumps(variant, sort_keys=True, default=str)
        if signature in seen_variants:
            continue
        seen_variants |= {signature}
        result = cast(
            dict[str, Any],
            search_ctrl.smart_search_from_parsed(
                parsed=variant,
                limit=candidate_limit,
                db=db,
                shopper_profile=shopper_profile or {},
                supplier_id=supplier_id,
            ),
        )
        for product in cast(list[dict[str, Any]], result.get("products") or []):
            product_id = int(product.get("id") or 0)
            if not product_id or product_id in seen_ids:
                continue
            seen_ids |= {product_id}
            collected.append(product)
            if len(collected) >= candidate_limit:
                break

        if len(collected) >= candidate_limit:
            break

    ranked = sorted(
        collected,
        key=lambda product: _style_similarity_score(product, parsed_filters, shopper_profile),
        reverse=True,
    )
    return ranked[:limit]


def _alternative_results_reply(parsed_filters: dict[str, Any], products: list[dict[str, Any]], lang: str = "en") -> str:
    subject = _product_subject(parsed_filters)
    lead = products[0]
    lead_category = str(lead.get("category") or "items").strip().lower()
    if lang == "ar":
        return (
            f"لا يتوفر {subject} مطابق تمامًا في المخزون الآن، لكن سحبت {len(products)} خيارًا قريبًا من فئة {lead_category} "
            f"يمكنك تسوّقه الآن. "
            + _category_sales_line(parsed_filters, products, "close", lang)
            + " "
            f"أبرز خيار: {_lead_product_line(lead)}. "
            + _result_guidance_line(parsed_filters, products, lang)
        )
    return (
        f"I don't have an exact {subject} in stock right now, but I pulled {len(products)} close {lead_category} option"
        f"{'s' if len(products) != 1 else ''} you can shop now. "
        + _category_sales_line(parsed_filters, products, "close", lang)
        + " "
        f"Best lead: {_lead_product_line(lead)}. "
        + _result_guidance_line(parsed_filters, products, lang)
    )


def _rounded_budget_prompt(value: Optional[float], lang: str = "en") -> Optional[str]:
    if value is None or value <= 0:
        return None
    if value < 100:
        rounded = int(round(value / 10.0) * 10)
    elif value < 500:
        rounded = int(round(value / 25.0) * 25)
    else:
        rounded = int(round(value / 50.0) * 50)
    rounded = max(rounded, 10)
    if lang == "ar":
        return f"اعرض خيارات تحت {rounded}"
    return f"Show options under {rounded}"


def _build_follow_up_prompts(
    intent: str,
    shopper_profile: dict[str, Any],
    parsed_filters: dict[str, Any],
    products: list[dict[str, Any]],
    lang: str = "en",
) -> list[str]:
    prompts: list[str] = []
    preferred_categories = cast(list[str], shopper_profile.get("preferred_categories") or [])
    preferred_brands = cast(list[str], shopper_profile.get("preferred_brands") or [])
    preferred_sizes = cast(list[str], shopper_profile.get("preferred_sizes") or [])
    preferred_price = cast(Optional[float], shopper_profile.get("preferred_price"))

    def add(prompt: Optional[str]) -> None:
        cleaned = str(prompt or "").strip()
        if not cleaned or cleaned in prompts:
            return
        prompts.append(cleaned)

    if intent == "product_search":
        if not parsed_filters.get("brand") and preferred_brands:
            add(f"اعرض خيارات {preferred_brands[0]}" if lang == "ar" else f"Show {preferred_brands[0]} options")
        if not parsed_filters.get("size") and preferred_sizes:
            add(f"أظهر فقط مقاس {preferred_sizes[0]}" if lang == "ar" else f"Only show size {preferred_sizes[0]}")
        if parsed_filters.get("sort") != "rating":
            add("اعرض الخيارات الأعلى تقييمًا" if lang == "ar" else "Show top-rated options")
        if parsed_filters.get("max_price") is None:
            add(_rounded_budget_prompt(preferred_price, lang))
        if products:
            lead_category = str(products[0].get("category") or "").strip()
            lead_brand = str(products[0].get("brand") or "").strip()
            if lead_category:
                add(f"اعرض المزيد من خيارات {lead_category.lower()}" if lang == "ar" else f"Show more {lead_category.lower()} picks")
            if lead_brand and not parsed_filters.get("brand"):
                add(f"اعرض المزيد من {lead_brand}" if lang == "ar" else f"Show more from {lead_brand}")
            if parsed_filters.get("color"):
                color_prompt = (
                    f"اعرض خيارات {parsed_filters['color']} {lead_category.lower()}" if lang == "ar" else f"Show {parsed_filters['color']} {lead_category.lower()} options"
                ) if lead_category else (
                    f"اعرض خيارات {parsed_filters['color']}" if lang == "ar" else f"Show {parsed_filters['color']} options"
                )
                add(color_prompt)
            add("اعرض بدائل أرخص" if lang == "ar" else "Show cheaper alternatives")
    else:
        if shopper_profile.get("has_history") and preferred_categories:
            add(f"اعرض المزيد من {preferred_categories[0]}" if lang == "ar" else f"Show me more {preferred_categories[0]}")
        if preferred_brands:
            add(f"اعرض عروض {preferred_brands[0]}" if lang == "ar" else f"Show me {preferred_brands[0]} deals")
        add(_rounded_budget_prompt(preferred_price, lang))
        add("اعرض المنتجات الأعلى تقييمًا" if lang == "ar" else "Show top-rated products")

    return prompts[:4]


def _last_product_filters(history: list[dict[str, Any]]) -> Optional[dict[str, Any]]:
    for item in reversed(history):
        if item.get("role") == "user" and item.get("intent") == "product_search" and item.get("filters"):
            return cast(dict[str, Any], item["filters"])
    return None


def _should_treat_as_product_search(message: str, intent: str, parsed_filters: dict[str, Any]) -> bool:
    if intent == "product_search":
        return True
    if intent != "unknown" or _NOISE_IN_PRODUCT.search(message):
        return False
    return bool(_PRODUCT_REQUEST_HINT.search(message)) or any(
        parsed_filters.get(key) not in (None, "", [])
        for key in ("category", "color", "min_price", "max_price", "min_rating", "quality")
    )


def _should_merge_product_filters(
    message: str,
    intent: str,
    parsed_filters: dict[str, Any],
    previous_filters: Optional[dict[str, Any]],
) -> bool:
    if not previous_filters or _NOISE_IN_PRODUCT.search(message):
        return False
    if intent not in {"unknown", "product_search"}:
        return False

    query_terms = cast(list[str], parsed_filters.get("terms") or [])
    has_structured_modifiers = any(
        parsed_filters.get(key) not in (None, "", [])
        for key in ("category", "color", "min_price", "max_price", "min_rating", "quality", "sort")
    )
    has_subject = any(term not in search_ctrl.COLOR_ALIASES.values() for term in query_terms)
    if intent == "product_search" and has_subject:
        return False
    return has_structured_modifiers or bool(_PRODUCT_REFERENCE_HINT.search(message)) or not has_subject


def _merge_product_filters(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key in ("min_price", "max_price", "category", "brand", "size", "color", "min_rating", "quality", "sort"):
        if incoming.get(key) not in (None, "", []):
            merged[key] = incoming[key]

    incoming_query = str(incoming.get("q") or "").strip()
    incoming_terms = cast(list[str], incoming.get("terms") or [])
    incoming_has_subject = any(term not in search_ctrl.COLOR_ALIASES.values() for term in incoming_terms)
    if incoming_query and incoming_has_subject:
        merged["q"] = incoming_query
        merged["terms"] = incoming.get("terms") or []
    else:
        merged["q"] = base.get("q") or ""
        merged["terms"] = base.get("terms") or []

    merged["raw_q"] = incoming.get("raw_q") or base.get("raw_q") or merged.get("q")
    return merged


def _product_subject(parsed_filters: dict[str, Any]) -> str:
    parts: list[str] = []
    brand = cast(Optional[str], parsed_filters.get("brand"))
    color = cast(Optional[str], parsed_filters.get("color"))
    query_text = str(parsed_filters.get("q") or "").strip()
    category = cast(Optional[str], parsed_filters.get("category"))

    if brand:
        parts.append(brand)
    if color:
        parts.append(color)
    if query_text:
        parts.append(query_text)
    elif category:
        parts.append(category)

    return " ".join(part for part in parts if part).strip() or "products"


def _product_constraints(parsed_filters: dict[str, Any], lang: str = "en") -> list[str]:
    constraints: list[str] = []
    min_price = cast(Optional[float], parsed_filters.get("min_price"))
    max_price = cast(Optional[float], parsed_filters.get("max_price"))
    size = cast(Optional[str], parsed_filters.get("size"))
    min_rating = cast(Optional[float], parsed_filters.get("min_rating"))
    quality = cast(Optional[str], parsed_filters.get("quality"))
    sort = cast(Optional[str], parsed_filters.get("sort"))

    ar = lang == "ar"
    if min_price is not None and max_price is not None:
        constraints.append(
            f"بين {_format_price_value(min_price)} و{_format_price_value(max_price)}" if ar
            else f"between {_format_price_value(min_price)} and {_format_price_value(max_price)}"
        )
    elif max_price is not None:
        constraints.append(f"تحت {_format_price_value(max_price)}" if ar else f"under {_format_price_value(max_price)}")
    elif min_price is not None:
        constraints.append(f"فوق {_format_price_value(min_price)}" if ar else f"over {_format_price_value(min_price)}")

    if size:
        constraints.append(f"مقاس {size}" if ar else f"size {size}")

    if min_rating is not None or quality == "top-rated":
        constraints.append("بتقييمات قوية" if ar else "with strong ratings")
    elif quality == "quality" or sort == "rating":
        constraints.append("مصنّفة حسب الجودة" if ar else "ranked by quality")
    elif sort == "newest":
        constraints.append("الأحدث أولًا" if ar else "newest first")
    elif sort == "price_asc":
        constraints.append("أقل سعر أولًا" if ar else "lowest price first")

    return constraints


def _product_results_reply(
    parsed_filters: dict[str, Any],
    products: list[dict[str, Any]],
    shopper_profile: Optional[dict[str, Any]] = None,
    lang: str = "en",
) -> str:
    subject = _product_subject(parsed_filters)
    constraints = _product_constraints(parsed_filters, lang)
    count = len(products)
    lead = products[0]
    constraint_line = f" I kept this focused on {', '.join(constraints)}." if constraints else ""
    ar_constraint_line = f" حافظت على تركيز النتائج على {', '.join(constraints)}." if constraints else ""
    if lang == "ar":
        return (
            f"سحبت {count} خيارًا قويًا لـ {subject} من أجلك.{ar_constraint_line} "
            + _category_sales_line(parsed_filters, products, "exact", lang)
            + " "
            f"أبرز خيار: {_lead_product_line(lead)}. "
            + _result_guidance_line(parsed_filters, products, lang)
            + _profile_personalization_hint(shopper_profile or {}, parsed_filters)
            + _upsell_hint(products, lang)
        )
    return (
        f"I pulled {count} strong {subject} option{'s' if count != 1 else ''} for you.{constraint_line} "
        + _category_sales_line(parsed_filters, products, "exact", lang)
        + " "
        f"Best lead: {_lead_product_line(lead)}. "
        + _result_guidance_line(parsed_filters, products, lang)
        + _profile_personalization_hint(shopper_profile or {}, parsed_filters)
        + _upsell_hint(products, lang)
    )


def record_product_click(
    db: Session,
    session_id: str,
    product_id: int,
    user_id: Optional[int] = None,
) -> None:
    if user_id is not None:
        record_product_view(db=db, user_id=user_id, product_id=product_id)
    _record_chatbot_event(
        db,
        session_id=session_id,
        event_type="product_click",
        user_id=user_id,
        clicked_product_id=product_id,
    )


# ─── Record browsing event ────────────────────────────────────────────────────
def record_product_view(db: Session, user_id: int, product_id: int) -> None:
    """Append to the user's browsing history (last 50 views, deduped)."""
    user = get_user_by_id(db, user_id)
    if not user:
        return
    history = _load_browsing_history(user)
    # Remove existing occurrence and prepend
    history = [pid for pid in history if pid != product_id]
    history.insert(0, product_id)
    history = history[:50]  # keep last 50
    setattr(user, "browsing_history_json", json.dumps(history))
    commit_only(db)


# ─── Main chatbot entry point ─────────────────────────────────────────────────
def handle_message(
    db: Session,
    message: str,
    user_id: Optional[int] = None,
    session_id: Optional[str] = None,
    supplier_id: Optional[int] = None,
    lang: str = "en",
) -> dict:
    """
    Process a chatbot message and return a structured reply.
    Returns: {reply: str, intent: str, products: list, session_id: str, suggested_prompts: list[str], result_mode: str}
    """
    if not message or not message.strip():
        empty_reply = "اكتب رسالة وسأبذل قصارى جهدي لمساعدتك! 😊" if lang == "ar" else "Please type a message and I'll do my best to help! 😊"
        return {
            "reply": empty_reply,
            "intent": "empty",
            "products": [],
            "session_id": session_id or "",
            "suggested_prompts": [],
            "result_mode": "none",
        }

    message = message.strip()[:500]  # limit length

    # ── Session history ────────────────────────────────────────────────────────
    active_session_id, history = _get_or_create_session(session_id)
    _append_to_session(active_session_id, "user", message)

    # Build context hint from recent history for follow-up detection
    recent_intents = [m.get("intent") for m in history[-4:] if m.get("role") == "user" and m.get("intent")]

    raw_intent = _classify_intent(message)
    intent = raw_intent
    products = []
    result_mode = "none"
    shopper_profile = get_shopper_profile(db, user_id)
    parsed_filters = search_ctrl.parse_query(message)
    previous_filters = _last_product_filters(history)

    if _should_merge_product_filters(message, raw_intent, parsed_filters, previous_filters):
        parsed_filters = _merge_product_filters(cast(dict[str, Any], previous_filters), parsed_filters)
        intent = "product_search"

    # Context-aware: if the previous intent was product_search and the current message is unclear,
    # treat it as a product refinement.
    if intent == "unknown" and "product_search" in recent_intents:
        intent = "product_search"

    if _should_treat_as_product_search(message, intent, parsed_filters):
        intent = "product_search"

    if intent == "product_search":
        search_result = search_products_with_context(
            db,
            parsed_filters,
            user_id=user_id,
            supplier_id=supplier_id,
        )
        parsed_filters = cast(dict[str, Any], search_result.get("parsed") or parsed_filters)
        products = cast(list[dict[str, Any]], search_result.get("products") or [])
        shopper_profile = cast(dict[str, Any], search_result.get("shopper_profile") or shopper_profile)
        if products:
            result_mode = "exact"
            reply = _product_results_reply(
                parsed_filters,
                products,
                shopper_profile=shopper_profile,
                lang=lang,
            )
        else:
            relaxed_products = _build_relaxed_product_recommendations(
                db,
                parsed_filters,
                shopper_profile=shopper_profile,
                supplier_id=supplier_id,
            )
            if relaxed_products:
                products = relaxed_products
                result_mode = "close"
                reply = _alternative_results_reply(parsed_filters, products, lang)
            else:
                reply = _catalog_guidance_reply(
                    db,
                    _product_subject(parsed_filters),
                    supplier_id=supplier_id,
                    lang=lang,
                )
    else:
        reply = _static_reply(intent, lang)
        if intent in {"greeting", "help"} and shopper_profile.get("has_history"):
            preferred_categories = cast(list[str], shopper_profile.get("preferred_categories") or [])
            if preferred_categories:
                reply += (
                    f" بناءً على نشاطك الأخير، يمكنني أيضًا عرض المزيد من خيارات {preferred_categories[0]}."
                    if lang == "ar"
                    else f" Based on your recent activity, I can also surface more {preferred_categories[0]} options for you."
                )

    suggested_prompts = _build_follow_up_prompts(
        intent, shopper_profile, parsed_filters, products, lang
    )

    # Store intent in history for follow-up context
    if active_session_id in _SESSION_HISTORY:
        msgs = _SESSION_HISTORY[active_session_id]["messages"]
        if msgs and msgs[-1]["role"] == "user":
            msgs[-1]["intent"] = intent
            if intent == "product_search":
                msgs[-1]["filters"] = parsed_filters

    _record_chatbot_event(
        db,
        session_id=active_session_id,
        event_type="query",
        user_id=user_id,
        message=message,
        normalized_query=str(parsed_filters.get("q") or message).strip(),
        intent=intent,
        filters=parsed_filters,
        result_count=len(products),
        product_ids=[int(product["id"]) for product in products if product.get("id")],
    )

    _append_to_session(active_session_id, "bot", reply)

    return {
        "reply": reply,
        "intent": intent,
        "products": products,
        "session_id": active_session_id,
        "suggested_prompts": suggested_prompts,
        "result_mode": result_mode,
    }

