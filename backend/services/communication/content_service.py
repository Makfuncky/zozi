
"""
Content services for the Dynamic Supplier Upload flow (Step 6):

* ``translate_en_to_ar`` — best-effort EN→AR translation. Uses Ollama
  (``phi3:mini``) when reachable; otherwise falls back to a curated
  e-commerce glossary so the feature never hard-fails.
* ``moderate_content`` — scans text for GCC-restricted items (alcohol,
  pork, gambling, tobacco) and returns a pass/fail verdict with reasons.

Both are intentionally dependency-free and safe to call from the request path.
"""


import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_TEXT_MODEL = "phi3:mini"

# Curated EN→AR glossary for the fallback translator (common e-commerce terms).
_GLOSSARY = {
    "product": "منتج", "products": "منتجات", "price": "السعر", "new": "جديد",
    "sale": "تخفيض", "free": "مجاني", "shipping": "شحن", "delivery": "توصيل",
    "fast": "سريع", "premium": "ممتاز", "quality": "جودة", "red": "أحمر",
    "blue": "أزرق", "black": "أسود", "white": "أبيض", "green": "أخضر",
    "size": "المقاس", "color": "اللون", "colour": "اللون", "warranty": "ضمان",
    "available": "متوفر", "order": "اطلب", "best": "الأفضل", "discount": "خصم",
    "offer": "عرض", "buy": "اشترِ", "watch": "ساعة", "phone": "هاتف",
    "dress": "فستان", "shirt": "قميص", "shoes": "أحذية", "bag": "حقيبة",
    "gold": "ذهبي", "silver": "فضي", "cotton": "قطني", "leather": "جلدي",
    "waterproof": "مقاوم للماء", "original": "أصلي", "style": "ستايل",
}

# Restricted-term → category used for moderation flags.
_RESTRICTED_KEYWORDS = {
    "alcohol": "alcohol", "wine": "alcohol", "beer": "alcohol", "liquor": "alcohol",
    "vodka": "alcohol", "whisky": "alcohol", "whiskey": "alcohol", "rum": "alcohol",
    "champagne": "alcohol", "pork": "pork", "bacon": "pork", "ham": "pork",
    "gambling": "gambling", "casino": "gambling", "bet": "gambling", "betting": "gambling",
    "lottery": "gambling", "cigar": "tobacco", "cigarette": "tobacco", "tobacco": "tobacco",
}


async def translate_en_to_ar(text: str) -> str:
    """Translate English text to Arabic. Ollama first, glossary fallback."""
    if not text or not text.strip():
        return ""
    try:
        import httpx  # noqa: F401

        prompt = (
            "Translate the following e-commerce product text into Arabic (Modern "
            "Standard Arabic). Reply with ONLY the Arabic translation, no quotes, "
            "no explanation:\n\n" + text
        )
        payload = {
            "model": _OLLAMA_TEXT_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": False,
            "options": {"num_predict": 500, "keep_alive": "5m"},
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(f"{_OLLAMA_BASE_URL}/v1/chat/completions", json=payload)
            if resp.status_code == 200:
                out = resp.json()["choices"][0]["message"]["content"].strip().strip('"')
                if out:
                    return out
    except Exception as exc:  # noqa: BLE001
        logger.info("content_service: Ollama translation unavailable (%s)", exc)
    return _glossary_fallback(text)


def _glossary_fallback(text: str) -> str:
    """Word-by-word substitution using the curated glossary (keeps structure)."""
    parts = re.split(r"(\s+)", text)
    out: List[str] = []
    for part in parts:
        low = part.lower().strip(".,!?;:")
        out.append(_GLOSSARY.get(low, part))
    return "".join(out)


def moderate_content(text: str = "", category: str = "") -> Dict[str, object]:
    """
    Scan text for GCC-restricted content.

    Returns ``{"passed": bool, "flags": list[str], "notice": str}``.
    """
    flags: List[str] = []
    low = (text or "").lower()
    for kw, reason in _RESTRICTED_KEYWORDS.items():
        if re.search(r"\b" + re.escape(kw) + r"\b", low):
            if reason not in flags:
                flags.append(reason)

    if flags:
        notice = (
            "Restricted content detected (" + ", ".join(flags) +
            "). This listing may be blocked in GCC markets. Review before publishing."
        )
        passed = False
    else:
        notice = "Content looks compliant for GCC markets."
        passed = True

    return {"passed": passed, "flags": flags, "notice": notice}

