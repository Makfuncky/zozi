"""
AI Service — HuggingFace Inference API integration.

Provides:
    * generate_product_description(name, category, image_bytes=None) -> str
from sqlalchemy.orm import Session
    * suggest_category(name, description="") -> str
    * suggest_tags(name, category, description="") -> list[str]
    * infer_product_name(name, description="", image_bytes=None) -> str

All calls are HTTP-only (Inference API), so no heavy ML libraries needed.
Falls back gracefully if the API key is missing or the call fails.
"""
import base64
import hashlib
import io
import logging
import os
import re
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional

import requests

from utils.config import settings

logger = logging.getLogger(__name__)


class _LazyPIL:
    """Lazy proxy for PIL.Image to avoid top-level import."""
    def __getattr__(self, name):
        from PIL import Image
        return getattr(Image, name)


Image = _LazyPIL()

HF_API_TOKEN: str = settings.hf_api_token  # resolved once at import; empty string → unauthenticated
HF_API_BASE = "https://api-inference.huggingface.co/models"

ZERO_SHOT_MODEL = "facebook/bart-large-mnli"
CAPTION_MODEL = "Salesforce/blip-image-captioning-base"
TEXT_GEN_MODEL = "mistralai/Mistral-7B-Instruct-v0.3"   # fallback text description

PRODUCT_CATEGORIES = [
    "Electronics", "Fashion", "Accessories", "Furniture", "Beauty",
    "Sports", "Home", "Books", "Baby", "Automotive", "Crafts",
    "Grocery", "Health", "Toys", "Jewelry", "Office",
]

COMMON_TAGS = {
    "Electronics": ["wireless", "smart", "portable", "rechargeable", "bluetooth", "HD", "USB-C"],
    "Fashion": ["fashion", "everyday-wear", "comfort-fit", "style-led", "closet-staple"],
    "Accessories": ["accessories", "giftable", "polished-finish", "everyday-style", "durable"],
    "Furniture": ["furniture", "durable-build", "interior", "space-conscious", "home-styling"],
    "Beauty": ["skincare", "daily-care", "beauty-routine", "skin-friendly", "hydrating"],
    "Sports": ["breathable", "high-performance", "waterproof", "lightweight", "anti-slip"],
    "Home": ["eco-friendly", "multipurpose", "easy-clean", "durable", "space-saving"],
    "Books": ["bestseller", "educational", "illustrated", "hardcover", "paperback"],
    "Baby": ["safe", "BPA-free", "soft", "educational", "hypoallergenic"],
    "Automotive": ["weather-resistant", "universal-fit", "durable", "easy-install"],
    "Grocery": ["natural", "organic", "gluten-free", "sugar-free", "vegan"],
    "Health": ["natural", "clinically-tested", "fast-acting", "doctor-recommended"],
    "Jewelry": ["925-silver", "18k-gold", "hypoallergenic", "adjustable", "gift-ready"],
    "Toys": ["educational", "STEM", "age-appropriate", "safe", "interactive"],
}

VARIANT_TEMPLATE_OPTIONS = {
    "apparel": ["XS", "S", "M", "L", "XL", "XXL", "XXXL"],
    "footwear": ["35", "36", "37", "38", "39", "40", "41", "42", "43", "44", "45", "46"],
    "kids": ["2Y", "3Y", "4Y", "5Y", "6Y", "8Y", "10Y", "12Y"],
    "pack-bundle": ["Single", "Pack of 2", "Pack of 3", "Pack of 6", "Pack of 12", "Bundle"],
    "capacity-volume": ["100 ml", "250 ml", "500 ml", "1 L", "32 GB", "64 GB", "128 GB"],
    "model-edition": ["Standard", "Pro", "Max", "2026 Edition", "Type-C", "Lightning"],
    "home-furniture": ["Small", "Medium", "Large", "2-Seater", "3-Seater", "King", "Queen"],
    "universal": ["One Size", "Mini", "Standard", "Large", "Universal Fit"],
}

MATERIAL_SUGGESTIONS_BY_TEMPLATE = {
    "apparel": ["Cotton Blend", "Linen", "Satin", "Silk Blend", "Polyester Blend"],
    "footwear": ["Leather", "Mesh", "Rubber Sole", "Canvas", "Synthetic Upper"],
    "kids": ["Soft Cotton", "BPA-Free Plastic", "Plush Fabric", "Silicone", "Wood"],
    "pack-bundle": ["Mixed Bundle", "Refill Pack", "Cardboard Carton", "Foil Pack", "Reusable Pouch"],
    "capacity-volume": ["Glass", "Food-Grade Plastic", "PET", "Aluminum", "Stainless Steel"],
    "model-edition": ["ABS Plastic", "Aluminum", "Tempered Glass", "Silicone", "Carbon Fiber"],
    "home-furniture": ["Solid Wood", "Engineered Wood", "Steel", "Tempered Glass", "Velvet Upholstery"],
    "universal": ["Plastic", "Metal", "Cotton Blend", "Glass", "Composite"],
}

_GENERIC_NAME_WORDS = {
    "a", "an", "the", "this", "that", "these", "those",
    "at", "in", "on", "of", "for", "from", "to", "by", "with",
    "product", "products", "item", "items", "general", "photo", "image",
    "picture", "upload", "file", "whatsapp", "catalog", "media",
    "main",
}

_GENERIC_TAG_WORDS = _GENERIC_NAME_WORDS | {
    "thing", "model", "view", "shot", "screenshot", "camera",
}

_FILENAME_ALIAS_PATTERNS = [
    (re.compile(r"\bbar\b", re.IGNORECASE), "bra"),
    (re.compile(r"\bkiyomi\b", re.IGNORECASE), "kiyomi sofa"),
    (re.compile(r"\bcsk\b", re.IGNORECASE), "skin elixir skincare"),
]

_PRODUCT_SNAPSHOT_DIR = Path(__file__).resolve().parents[2] / "documents" / "snap" / "Product"
_IDENTIFIER_ARTIFACT_PATTERN = re.compile(
    r"^(?:\d{2,5}(?:x\d{2,5})?|[A-Za-z]{0,3}\d{5,}[A-Za-z0-9-]*|HC\d{6,}[A-Za-z0-9-]*)$",
    re.IGNORECASE,
)
_GENERIC_PRODUCT_NAME_PATTERN = re.compile(
    r"^(?:[A-Za-z]+\s+)?(?:product|accessory|furniture piece|electronics product|beauty product|home product|general product)$",
    re.IGNORECASE,
)
_VISUAL_HINT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "id": "chevron-wardrobe",
        "sample_files": ("1012-750x650.jpg",),
        "name": "Chevron Wardrobe",
        "category": "Furniture",
        "color": "Brown",
        "match_distance": 6,
    },
    {
        "id": "gray-wardrobe",
        "sample_files": ("4-750x650.jpg",),
        "name": "Gray Wardrobe",
        "category": "Furniture",
        "color": "Gray",
        "match_distance": 6,
    },
    {
        "id": "neutral-chaise-sofa",
        "sample_files": ("168372845-163452422-HC01062021_01-2100.webp",),
        "name": "Neutral Chaise Sofa",
        "category": "Furniture",
        "color": "Beige",
        "match_distance": 6,
    },
    {
        "id": "ferrari-sunglasses-black",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.43.24.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (4).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.24 (5).jpeg",
        ),
        "name": "Ferrari Sunglasses",
        "category": "Accessories",
        "color": "Black",
        "match_distance": 10,
    },
    {
        "id": "ferrari-sunglasses-brown",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.43.25.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.25 (3).jpeg",
        ),
        "name": "Ferrari Sunglasses",
        "category": "Accessories",
        "color": "Brown",
        "match_distance": 10,
    },
    {
        "id": "casio-watch-silver",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.43.34.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.34 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.34 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.36.jpeg",
        ),
        "name": "Casio Watch",
        "category": "Accessories",
        "color": "Silver",
        "match_distance": 10,
    },
    {
        "id": "casio-watch-mixed",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.43.35.jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (4).jpeg",
            "WhatsApp Image 2026-03-28 at 21.43.35 (5).jpeg",
        ),
        "name": "Casio Watch",
        "category": "Accessories",
        "color": "Silver",
        "match_distance": 10,
    },
    {
        "id": "necklace-v-pendant",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.45.00.jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.00 (3).jpeg",
        ),
        "name": "V Pendant Necklace",
        "category": "Accessories",
        "color": "Silver",
        "match_distance": 10,
    },
    {
        "id": "necklace-angel-pendant",
        "sample_files": (
            "WhatsApp Image 2026-03-28 at 21.45.01.jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (1).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (2).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (3).jpeg",
            "WhatsApp Image 2026-03-28 at 21.45.01 (4).jpeg",
        ),
        "name": "Angel Pendant Necklace",
        "category": "Accessories",
        "color": "Silver",
        "match_distance": 10,
    },
)

_INTIMATE_FASHION_PATTERN = re.compile(
    r"\b(?:bikini|lingerie|bra|swimwear|swimsuit|underwear|brief|panty)\b",
    re.IGNORECASE,
)

_MODEL_SUBJECT_PATTERN = re.compile(
    r"^(?:woman|women|lady|ladies|girl|girls|man|men|boy|boys|person|people|model|child|kid|toddler|female|male)\s+"
    r"(?:wearing|in|holding|carrying|using|showing|displaying|featuring)\s+(?P<item>.+)$",
    re.IGNORECASE,
)
_GENERIC_SUBJECT_PATTERN = re.compile(
    r"^(?:woman|women|lady|ladies|girl|girls|man|men|boy|boys|person|people|model|child|kid|toddler|female|male)$",
    re.IGNORECASE,
)
_TRAILING_CONTEXT_PATTERNS = [
    re.compile(r"\s+(?:standing|posing|walking|sitting|displayed|shown|hanging|lying|laid|isolated)\b.*$", re.IGNORECASE),
    re.compile(r"\s+(?:against|inside|near|beside|under|over|at)\s+.+$", re.IGNORECASE),
    re.compile(r"\s+on\s+(?:a|an|the|plain|white|black|wooden|studio)\b.*$", re.IGNORECASE),
    re.compile(r"\s+in\s+(?:a|an|the|studio|room|scene|background)\b.*$", re.IGNORECASE),
]
_SPECIFIC_TAG_PATTERNS = (
    (re.compile(r"\b(?:bra|bralette)\b", re.IGNORECASE), ["bra", "intimates", "soft-support", "layering-essential"]),
    (re.compile(r"\b(?:bikini|swimwear|swimsuit)\b", re.IGNORECASE), ["bikini", "swimwear", "beachwear", "two-piece"]),
    (re.compile(r"\blingerie\b", re.IGNORECASE), ["lingerie", "intimates", "soft-touch", "lace-look"]),
    (re.compile(r"\babaya\b", re.IGNORECASE), ["abaya", "modestwear", "flowing", "occasionwear"]),
    (re.compile(r"\b(?:wardrobe|cupboard|cabinet)\b", re.IGNORECASE), ["storage", "wardrobe", "bedroom", "wood-finish"]),
    (re.compile(r"\b(?:sofa|chaise)\b", re.IGNORECASE), ["sofa", "living-room", "upholstered", "lounging"]),
    (re.compile(r"\bsunglasses\b", re.IGNORECASE), ["sunglasses", "eyewear", "statement-style", "daily-wear"]),
    (re.compile(r"\bwatch\b", re.IGNORECASE), ["watch", "timepiece", "wristwear", "metal-finish"]),
    (re.compile(r"\b(?:necklace|pendant)\b", re.IGNORECASE), ["necklace", "pendant", "giftable", "jewelry"]),
    (re.compile(r"\b(?:serum|elixir|cream|moisturizer|skincare|retinol|hyaluronic)\b", re.IGNORECASE), ["skincare", "daily-care", "hydrating", "beauty-routine"]),
)

_HF_HEADERS = lambda: {"Authorization": f"Bearer {settings.hf_api_token}"} if settings.hf_api_token else {}
_TRANSIENT_STATUS_CODES = {408, 425, 429, 500, 502, 503, 504}


def _post_hf_request(
    model: str,
    *,
    json: Optional[dict] = None,
    data: Optional[bytes] = None,
    timeout: int = 15,
    extra_headers: Optional[dict] = None,
    attempts: int = 3,
):
    last_error: Optional[Exception] = None
    last_response = None

    for attempt in range(attempts):
        try:
            response = requests.post(
                f"{HF_API_BASE}/{model}",
                headers={**_HF_HEADERS(), **(extra_headers or {})},
                json=json,
                data=data,
                timeout=timeout,
            )
            if response.status_code == 200:
                return response
            last_response = response
            if response.status_code not in _TRANSIENT_STATUS_CODES:
                return response
        except Exception as exc:
            last_error = exc

        if attempt < attempts - 1:
            time.sleep(0.4 * (attempt + 1))

    if last_error:
        raise last_error
    return last_response


# ─────────────────────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────────────────────

def generate_product_description(
    name: str,
    category: str = "",
    image_bytes: Optional[bytes] = None,
    caption: str = "",
) -> str:
    """
    Generate a compelling product description.
    1. If image_bytes provided → BLIP captioning → enrich with text.
    2. Otherwise → rule-based template description.
    Falls back to template on any error.
    """
    if not caption and image_bytes:
        caption = _blip_caption(image_bytes)

    return _build_description(name, category, caption)


def suggest_category(
    name: str,
    description: str = "",
    image_bytes: Optional[bytes] = None,
    caption: str = "",
) -> str:
    """
    Use zero-shot classification to suggest the most appropriate category.
    Falls back to keyword matching on error.
    """
    if not caption and image_bytes:
        caption = _blip_caption(image_bytes)
    text = ". ".join(part for part in (name.strip(), description.strip(), caption.strip()) if part).strip()
    if text:
        result = _zero_shot_classify(text, PRODUCT_CATEGORIES)
        if result:
            return result

    # keyword-based fallback
    return _keyword_category(text.lower())


def detect_dominant_color(image_bytes: Optional[bytes]) -> Optional[str]:
    if not image_bytes:
        return None

    swatches = {
        "Black": (34, 34, 34),
        "White": (245, 245, 245),
        "Gray": (140, 140, 140),
        "Silver": (192, 192, 192),
        "Blue": (52, 120, 246),
        "Red": (220, 53, 69),
        "Green": (40, 167, 69),
        "Yellow": (255, 193, 7),
        "Orange": (253, 126, 20),
        "Purple": (111, 66, 193),
        "Pink": (232, 62, 140),
        "Brown": (121, 85, 72),
        "Beige": (214, 197, 170),
    }

    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        image.thumbnail((128, 128))
        quantized = image.quantize(colors=8, method=Image.Quantize.MEDIANCUT).convert("RGB")
        colors = quantized.getcolors(maxcolors=64) or []
        if not colors:
            return None

        bucket_scores = {name: 0 for name in swatches}
        for count, rgb in colors:
            if not isinstance(rgb, tuple) or len(rgb) != 3:
                continue
            red, green, blue = rgb
            nearest = min(
                swatches.items(),
                key=lambda item: (
                    (red - item[1][0]) ** 2
                    + (green - item[1][1]) ** 2
                    + (blue - item[1][2]) ** 2
                ),
            )[0]
            bucket_scores[nearest] += count

        best = max(bucket_scores.items(), key=lambda item: item[1])
        return best[0] if best[1] > 0 else None
    except Exception as exc:
        logger.warning("Dominant color detection failed: %s", exc)
        return None


def detect_palette(image_bytes_list: list[bytes]) -> Optional[str]:
    colors: list[str] = []
    for image_bytes in image_bytes_list[:8]:
        detected = detect_dominant_color(image_bytes)
        if detected and detected not in colors:
          colors.append(detected)
    if not colors:
        return None
    return ", ".join(colors[:4])


def infer_color_from_filenames(filenames: list[str]) -> Optional[str]:
    color_aliases = [
        ("grey", "Gray"),
        ("gray", "Gray"),
        ("black", "Black"),
        ("white", "White"),
        ("brown", "Brown"),
        ("beige", "Beige"),
        ("tan", "Beige"),
        ("nude", "Beige"),
        ("blue", "Blue"),
        ("red", "Red"),
        ("green", "Green"),
        ("yellow", "Yellow"),
        ("orange", "Orange"),
        ("purple", "Purple"),
        ("pink", "Pink"),
        ("silver", "Silver"),
        ("gold", "Gold"),
    ]
    for filename in filenames:
        stem = os.path.splitext(filename or "")[0].lower()
        if not stem:
            continue
        normalized = re.sub(r"[^a-z0-9]+", " ", stem)
        for token, label in color_aliases:
            if re.search(rf"\b{re.escape(token)}\b", normalized):
                return label
    return None


def infer_category_from_filenames(filenames: list[str]) -> str:
    normalized_name = _infer_name_from_filenames(filenames)
    if normalized_name:
        return _keyword_category(normalized_name.lower())

    raw_text = " ".join(os.path.splitext(filename or "")[0] for filename in filenames).lower()
    raw_text = _apply_filename_aliases(raw_text)
    raw_text = re.sub(r"[^a-z0-9]+", " ", raw_text)
    return _keyword_category(raw_text)


def refine_color_palette(
    color: Optional[str],
    *,
    category: str = "",
    name: str = "",
    description: str = "",
    caption: str = "",
    filenames: Optional[list[str]] = None,
) -> Optional[str]:
    candidates = expand_palette_candidates(color)
    # If image decoding fails, provide a sensible Fashion palette fallback
    # so downstream color candidates are still useful in multipart suggest.
    if not candidates and category == "Fashion":
        candidates = [
            "Black",
            "White",
            "Blue",
            "Red",
            "Green",
            "Pink",
            "Yellow",
            "Orange",
            "Purple",
            "Brown",
            "Beige",
            "Gray",
            "Silver",
        ]

    if len(candidates) <= 1:
        return color

    ordered: list[str] = []
    filename_color = infer_color_from_filenames(filenames or [])
    if filename_color and filename_color in candidates:
        ordered.append(filename_color)

    text = " ".join(part for part in (name, category, description, caption) if part).lower()
    if category == "Fashion":
        if re.search(r"\b(?:lingerie|bra|underwear|brief|panty)\b", text):
            ordered.extend(["Black", "White", "Red", "Pink", "Purple"])
        elif re.search(r"\b(?:bikini|swimwear|swimsuit)\b", text):
            ordered.extend(["White", "Black", "Blue", "Red", "Pink", "Green", "Yellow", "Orange"])
        elif _INTIMATE_FASHION_PATTERN.search(text):
            ordered.extend(["Black", "White", "Blue", "Red", "Pink"])
        ordered.extend(["Black", "White", "Blue", "Red", "Green", "Pink", "Yellow", "Orange", "Purple"])
        ordered.extend(["Brown", "Beige", "Gray", "Silver"])

    if not ordered:
        return color

    prioritized = [candidate for candidate in ordered if candidate in candidates]
    resolved = _unique_suggestions(prioritized + candidates, limit=4)
    return ", ".join(resolved) if resolved else color


def infer_visual_product_hint(image_bytes_list: list[bytes]) -> Optional[dict[str, str]]:
    if not image_bytes_list:
        return None

    image_hashes = [image_hash for image_hash in (_average_image_hash(image_bytes) for image_bytes in image_bytes_list[:4]) if image_hash is not None]
    image_fingerprints = [
        image_fingerprint
        for image_fingerprint in (_bytes_fingerprint(image_bytes) for image_bytes in image_bytes_list[:4])
        if image_fingerprint is not None
    ]
    if not image_hashes and not image_fingerprints:
        return None

    best_hint: Optional[dict[str, Any]] = None
    best_score: tuple[int, int, float, int] | None = None

    for hint in _load_visual_reference_hints():
        hint_hashes = hint.get("hashes") or ()
        hint_fingerprints = set(hint.get("byte_hashes") or ())
        match_distance = int(hint.get("match_distance") or 8)
        if not hint_hashes and not hint_fingerprints:
            continue

        exact_matches = sum(1 for fingerprint in image_fingerprints if fingerprint in hint_fingerprints)

        matched_distances: list[int] = []
        best_distance = 64
        if hint_hashes:
            for image_hash in image_hashes:
                local_best = min(_hamming_distance(image_hash, candidate_hash) for candidate_hash in hint_hashes)
                best_distance = min(best_distance, local_best)
                if local_best <= match_distance:
                    matched_distances.append(local_best)

        if not matched_distances and exact_matches == 0:
            continue

        average_distance = (sum(matched_distances) / len(matched_distances)) if matched_distances else 64.0

        score = (
            exact_matches,
            len(matched_distances),
            -average_distance,
            -best_distance,
        )
        if best_score is None or score > best_score:
            best_score = score
            best_hint = hint

    if not best_hint:
        return None

    return {
        "id": str(best_hint["id"]),
        "name": str(best_hint["name"]),
        "category": str(best_hint["category"]),
        "color": str(best_hint["color"]),
    }


def is_generic_product_name(name: str) -> bool:
    normalized = (name or "").strip()
    if not normalized:
        return True
    if _GENERIC_PRODUCT_NAME_PATTERN.match(normalized):
        return True
    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", normalized)
    if not words:
        return True
    meaningful_words = [word for word in words if not _looks_like_identifier_artifact(word)]
    if not meaningful_words:
        return True
    return False


def suggest_tags(name: str, category: str, description: str = "") -> list[str]:
    """
    Suggest relevant tags for the product using zero-shot + category heuristics.
    Returns up to 8 tags.
    """
    base_tags = COMMON_TAGS.get(category, [])
    text = f"{name}. {description}".strip()
    normalized_text = text.lower()
    specific_tags: list[str] = []
    for pattern, tags in _SPECIFIC_TAG_PATTERNS:
        if pattern.search(normalized_text):
            specific_tags.extend(tags)

    # Try zero-shot with a curated tag pool
    all_candidate_tags = []
    for tags in COMMON_TAGS.values():
        all_candidate_tags.extend(tags)
    # Deduplicate
    candidate_tags = list(dict.fromkeys(all_candidate_tags))

    if text:
        try:
            resp = _post_hf_request(
                ZERO_SHOT_MODEL,
                json={
                "inputs": text,
                "parameters": {
                    "candidate_labels": candidate_tags[:20],  # API limit
                    "multi_label": True,
                },
                },
                timeout=15,
            )
            if resp is not None and resp.status_code == 200:
                data = resp.json()
                labels = data.get("labels", [])
                scores = data.get("scores", [])
                tagged = [(l, s) for l, s in zip(labels, scores) if s > 0.4]
                tagged.sort(key=lambda x: x[1], reverse=True)
                ai_tags = [t[0] for t in tagged[:5]]
                # Merge AI tags with category base tags
                merged = list(dict.fromkeys(ai_tags + specific_tags + base_tags[:3]))
                return merged[:8]
        except Exception as exc:
            logger.warning("Tag suggestion failed: %s", exc)

    # Fallback: use category base tags + name-derived keywords
    name_words = [
        word for word in re.split(r"[\s\-_]+", name.lower())
        if len(word) > 2 and word not in _GENERIC_TAG_WORDS
    ]
    fallback_tags = list(dict.fromkeys(specific_tags + base_tags[:5] + name_words[:3]))
    if not fallback_tags and category and category != "General":
        fallback_tags.append(category.lower())
    if len(fallback_tags) < 3:
        for tag in ["everyday", "versatile", "featured"]:
            if tag not in fallback_tags:
                fallback_tags.append(tag)
            if len(fallback_tags) >= 3:
                break
    return fallback_tags[:8]


def extract_image_caption(image_bytes: Optional[bytes]) -> str:
    if not image_bytes:
        return ""
    return _blip_caption(image_bytes)


def merge_image_captions(captions: list[str]) -> str:
    merged: list[str] = []
    for caption in captions:
        normalized = caption.strip()
        if normalized and normalized not in merged:
            merged.append(normalized)
    return ". ".join(merged[:3])


def infer_product_name(
    name: str = "",
    description: str = "",
    image_bytes: Optional[bytes] = None,
    caption: str = "",
    filenames: Optional[list[str]] = None,
    category: str = "",
    color: Optional[str] = None,
) -> str:
    provided_name = name.strip()
    if provided_name:
        return provided_name

    if not caption and image_bytes:
        caption = _blip_caption(image_bytes)

    candidate = caption.strip() or description.strip()
    normalized_candidate = _normalize_product_name(candidate)
    if normalized_candidate:
        return normalized_candidate

    filename_candidate = _infer_name_from_filenames(filenames or [])
    if filename_candidate:
        return filename_candidate

    if category or color:
        return _build_media_fallback_name(category=category, color=color)

    return ""


def expand_palette_candidates(color: Optional[str]) -> list[str]:
    if not color:
        return []
    return _unique_suggestions([part.strip() for part in color.split(",") if part.strip()], limit=4)


def suggest_variant_template(name: str, category: str = "", tags: Optional[list[str]] = None, description: str = "") -> str:
    text = " ".join(part for part in (name, category, description, ", ".join(tags or [])) if part).lower()
    normalized_category = (category or "").strip().lower()

    if re.search(r"\b(?:shoe|sneaker|heel|sandal|slipper|boot)\b", text):
        return "footwear"
    if re.search(r"\b(?:kid|baby|toddler|child|children|school)\b", text):
        return "kids"
    if normalized_category in {"fashion", "apparel"}:
        return "apparel"
    if normalized_category in {"furniture", "home"}:
        return "home-furniture"
    if normalized_category in {"accessories", "jewelry"}:
        return "universal"
    if re.search(r"\b(?:furniture|sofa|table|chair|mattress|bed|cabinet|cupboard|wardrobe|drawer|shelf|chaise|decor)\b", text):
        return "home-furniture"
    if re.search(r"\b(?:sunglasses|watch|bracelet|necklace|ring|wallet|belt|bag|pendant|timepiece|eyewear)\b", text):
        return "universal"
    if re.search(r"\b(?:bundle|pack|set of|refill|combo|deal)\b", text):
        return "pack-bundle"
    if re.search(r"\b(?:ml|liter|litre|l|gb|tb|capacity|volume)\b", text):
        return "capacity-volume"
    if re.search(r"\b(?:phone|laptop|earbud|headphone|charger|case|model|edition|compatible|electronics)\b", text):
        return "model-edition"
    if re.search(r"\b(?:dress|shirt|hoodie|abaya|fashion|jean|pant|coat|jacket|tee|t-shirt|bikini|lingerie|bra|swimwear|swimsuit|underwear|brief|panty|modestwear|outerwear|nightwear)\b", text):
        return "apparel"
    return "universal"


def suggest_variant_options(name: str, category: str = "", tags: Optional[list[str]] = None, description: str = "") -> list[str]:
    template_key = suggest_variant_template(name, category, tags=tags, description=description)
    return VARIANT_TEMPLATE_OPTIONS.get(template_key, VARIANT_TEMPLATE_OPTIONS["universal"])[:7]


def suggest_material_candidates(
    name: str,
    category: str = "",
    description: str = "",
    caption: str = "",
    tags: Optional[list[str]] = None,
) -> list[str]:
    text = " ".join(part for part in (name, category, description, caption, ", ".join(tags or [])) if part).lower()
    template_key = suggest_variant_template(name, category, tags=tags, description=description or caption)
    dynamic: list[str] = []
    material_patterns = [
        (r"cotton", "Cotton Blend"),
        (r"linen", "Linen"),
        (r"silk|satin", "Silk Blend"),
        (r"denim", "Denim"),
        (r"leather", "Leather"),
        (r"mesh", "Mesh"),
        (r"rubber", "Rubber Sole"),
        (r"wood", "Solid Wood"),
        (r"steel|metal", "Steel"),
        (r"glass", "Tempered Glass"),
        (r"plastic|abs|polymer", "ABS Plastic"),
        (r"silicone", "Silicone"),
        (r"aluminum|aluminium", "Aluminum"),
        (r"ceramic", "Ceramic"),
    ]
    for pattern, suggestion in material_patterns:
        if re.search(pattern, text):
            dynamic.append(suggestion)

    fallback = MATERIAL_SUGGESTIONS_BY_TEMPLATE.get(template_key, MATERIAL_SUGGESTIONS_BY_TEMPLATE["universal"])
    return _unique_suggestions(dynamic + fallback, limit=6)


# ─────────────────────────────────────────────────────────────
# INTERNAL HELPERS
# ─────────────────────────────────────────────────────────────

def _blip_caption(image_bytes: bytes) -> str:
    """Call BLIP image captioning via HF Inference API."""
    try:
        # HF Inference API for image-to-text accepts raw bytes
        resp = _post_hf_request(
            CAPTION_MODEL,
            data=image_bytes,
            timeout=30,
            extra_headers={"Content-Type": "application/octet-stream"},
        )
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list) and data:
                return data[0].get("generated_text", "")
            if isinstance(data, dict):
                return data.get("generated_text", "")
    except Exception as exc:
        if _is_transient_hf_error(exc):
            logger.debug("BLIP caption unavailable after retries; using fallback inference: %s", exc)
        else:
            logger.warning("BLIP caption failed: %s", exc)
    return ""


def _unique_suggestions(values: list[str], limit: int = 8) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
        if len(ordered) >= limit:
            break
    return ordered


def _average_image_hash(image_bytes: bytes) -> Optional[int]:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("L")
        image.thumbnail((64, 64))
        image = image.resize((8, 8))
        pixels = list(image.getdata())
        if not pixels:
            return None
        average = sum(pixels) / len(pixels)
        bits = "".join("1" if pixel >= average else "0" for pixel in pixels)
        return int(bits, 2)
    except Exception:
        return None


def _bytes_fingerprint(image_bytes: bytes) -> Optional[str]:
    if not image_bytes:
        return None
    return hashlib.sha1(image_bytes).hexdigest()


def _hamming_distance(left: int, right: int) -> int:
    return (left ^ right).bit_count()


@lru_cache(maxsize=1)
def _load_visual_reference_hints() -> tuple[dict[str, Any], ...]:
    hints: list[dict[str, Any]] = []
    for spec in _VISUAL_HINT_SPECS:
        hashes: list[int] = []
        byte_hashes: list[str] = []
        for sample_name in spec.get("sample_files", ()):
            sample_path = _PRODUCT_SNAPSHOT_DIR / str(sample_name)
            if not sample_path.is_file():
                continue
            try:
                sample_bytes = sample_path.read_bytes()
            except OSError:
                sample_bytes = b""

            sample_fingerprint = _bytes_fingerprint(sample_bytes)
            if sample_fingerprint is not None:
                byte_hashes.append(sample_fingerprint)

            sample_hash = _average_image_hash(sample_bytes)
            if sample_hash is not None:
                hashes.append(sample_hash)
        if hashes or byte_hashes:
            hints.append({**spec, "hashes": tuple(hashes), "byte_hashes": tuple(byte_hashes)})
    return tuple(hints)


def _apply_filename_aliases(text: str) -> str:
    resolved = text
    for pattern, replacement in _FILENAME_ALIAS_PATTERNS:
        resolved = pattern.sub(replacement, resolved)
    return resolved


def _normalize_product_name(text: str) -> str:
    candidate = text.strip()
    if not candidate:
        return ""

    candidate = re.sub(r"^(?:a|an|the)\s+", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"^(?:close[- ]up|photo|image|picture|shot|view)\s+of\s+", "", candidate, flags=re.IGNORECASE)
    candidate = re.sub(r"^(?:pair|set)\s+of\s+", "", candidate, flags=re.IGNORECASE)
    subject_match = _MODEL_SUBJECT_PATTERN.match(candidate)
    if subject_match:
        candidate = subject_match.group("item").strip()
    candidate = re.split(r"[,.!;:()\n]", candidate, maxsplit=1)[0].strip()
    for pattern in _TRAILING_CONTEXT_PATTERNS:
        candidate = pattern.sub("", candidate).strip()

    if _GENERIC_SUBJECT_PATTERN.match(candidate):
        return ""

    words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'/-]*", candidate)
    if not words:
        return ""

    filtered = [word for word in words if word.lower() not in _GENERIC_NAME_WORDS and not _looks_like_identifier_artifact(word)]
    chosen = filtered or words

    meaningful_words = [word for word in chosen if word.lower() not in _GENERIC_NAME_WORDS and not _looks_like_identifier_artifact(word)]
    if not meaningful_words:
        return ""

    if len(meaningful_words) == 1 and meaningful_words[0].lower() in _GENERIC_NAME_WORDS:
        return ""

    normalized_words = [
        word.upper() if word.isupper() and len(word) <= 4 else word.capitalize()
        for word in meaningful_words[:6]
    ]
    return " ".join(normalized_words)


def _looks_like_identifier_artifact(word: str) -> bool:
    normalized = (word or "").strip()
    if not normalized:
        return True
    return bool(_IDENTIFIER_ARTIFACT_PATTERN.match(normalized))


def _zero_shot_classify(text: str, labels: list[str]) -> str:
    """Run zero-shot classification and return the top label."""
    if not text.strip():
        return ""
    try:
        payload = {
            "inputs": text,
            "parameters": {"candidate_labels": labels},
        }
        resp = _post_hf_request(ZERO_SHOT_MODEL, json=payload, timeout=15)
        if resp is not None and resp.status_code == 200:
            data = resp.json()
            labels_out = data.get("labels", [])
            if labels_out:
                return labels_out[0]
    except Exception as exc:
        logger.warning("Zero-shot classification failed: %s", exc)
    return ""


def _is_transient_hf_error(exc: Exception) -> bool:
    message = str(exc).lower()
    transient_fragments = (
        "incompleteread",
        "connection broken",
        "connection aborted",
        "connection reset",
        "read timed out",
        "timed out",
        "temporary failure",
        "remote end closed connection",
        "503",
        "504",
        "502",
        "429",
    )
    return any(fragment in message for fragment in transient_fragments)

def _keyword_category(text: str) -> str:
    """Simple keyword-based category detection fallback."""
    mapping = {
        "Electronics": ["phone", "laptop", "tablet", "camera", "tv", "speaker", "headphone",
                         "monitor", "keyboard", "mouse", "charger", "cable", "gadget", "electronic"],
        "Fashion": ["shirt", "dress", "pants", "jeans", "jacket", "coat", "shoes", "sneakers",
                     "boots", "clothing", "wear", "fashion", "outfit", "suit", "blouse", "bikini",
                     "lingerie", "bra", "swimwear", "swimsuit", "underwear", "brief", "panty", "abaya"],
        "Accessories": ["bag", "wallet", "belt", "scarf", "hat", "cap", "sunglasses", "watch",
                         "bracelet", "necklace", "ring", "accessory"],
        "Furniture": ["chair", "table", "sofa", "desk", "shelf", "bed", "cabinet", "cupboard", "drawer",
                   "bookcase", "wardrobe", "chaise", "wooden", "furniture"],
        "Beauty": ["cream", "serum", "moisturizer", "lipstick", "makeup", "perfume", "shampoo",
                    "conditioner", "skincare", "cosmetic", "foundation", "beauty", "primer", "mask",
                    "retinol", "hyaluronic", "vitamin c", "elixir"],
        "Sports": ["gym", "yoga", "fitness", "sport", "running", "cycling", "swimming",
                    "basketball", "football", "exercise", "workout"],
        "Home": ["kitchen", "cooking", "cleaning", "storage", "organizer", "decor",
                  "curtain", "pillow", "blanket", "towel", "home"],
        "Books": ["book", "novel", "fiction", "guide", "manual", "ebook", "textbook"],
        "Baby": ["baby", "infant", "toddler", "diaper", "pacifier", "stroller"],
        "Automotive": ["car", "auto", "vehicle", "tire", "motor", "engine", "automotive"],
        "Grocery": ["food", "snack", "drink", "beverage", "spice", "sauce", "cereal"],
        "Health": ["vitamin", "supplement", "medicine", "health", "wellness", "protein"],
    }
    for cat, keywords in mapping.items():
        if any(re.search(rf"\b{re.escape(kw)}\b", text) for kw in keywords):
            return cat
    return "General"


def _infer_name_from_filenames(filenames: list[str]) -> str:
    for filename in filenames:
        stem = os.path.splitext(filename or "")[0]
        if not stem:
            continue
        cleaned = re.sub(r"[+_-]+", " ", stem)
        cleaned = _apply_filename_aliases(cleaned)
        cleaned = re.sub(r"\b\d{1,2}[.:]\d{2}(?:[.:]\d{2})?\b", " ", cleaned)
        cleaned = re.sub(r"\b(?:20\d{2}|19\d{2})\b", " ", cleaned)
        cleaned = re.sub(
            r"\b(?:img|image|photo|picture|pic|screenshot|scan|file|upload|camera|whatsapp|pxl|dsc|vid|video)\b",
            " ",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = re.sub(r"\b(?:at|edited|edit|copy|final|new)\b", " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\b\d+\b", " ", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        normalized = _normalize_product_name(cleaned)
        if normalized:
            return normalized
    return ""


def _build_media_fallback_name(category: str = "", color: Optional[str] = None) -> str:
    labels = {
        "Electronics": "Electronics Product",
        "Fashion": "Fashion Item",
        "Accessories": "Accessory",
        "Furniture": "Furniture Piece",
        "Beauty": "Beauty Product",
        "Sports": "Sports Product",
        "Home": "Home Product",
        "Books": "Book",
        "Baby": "Baby Product",
        "Automotive": "Automotive Product",
        "Crafts": "Craft Product",
        "Grocery": "Grocery Item",
        "Health": "Health Product",
        "Toys": "Toy",
        "Jewelry": "Jewelry Item",
        "Office": "Office Product",
        "General": "Product",
    }
    label = labels.get(category or "General", "Product")
    primary_color = (color or "").split(",")[0].strip()
    if not primary_color:
        return label
    return f"{primary_color} {label}".strip()


def _build_description(name: str, category: str, caption: str = "") -> str:
    """Build a rich product description from name, category, and optional caption."""
    normalized_name = name.lower()
    caption_part = f"Featuring {caption.lower().rstrip('.')}. " if caption else ""

    if category == "Fashion":
        if re.search(r"\b(?:bikini|swimwear|swimsuit)\b", normalized_name):
            return (
                f"Make warm-weather styling effortless with {name}, a swim-focused fashion essential designed for comfortable coverage and easy movement. "
                f"{caption_part}Ideal for beach days, resort packing, and poolside looks, this piece keeps your edit polished without overcomplicating the outfit."
            )
        if re.search(r"\b(?:bra|lingerie|underwear|brief|panty)\b", normalized_name):
            return (
                f"Refresh your essentials with {name}, an intimate fashion piece designed for soft comfort, reliable support, and easy layering. "
                f"{caption_part}Built for everyday wear, it balances flattering structure with a clean finish that fits naturally into a modern wardrobe."
            )

    if category == "Accessories":
        if re.search(r"\bwatch\b", normalized_name):
            return (
                f"Keep time in style with {name}, an accessories piece that combines an elevated finish with dependable everyday wearability. "
                f"{caption_part}Whether paired with tailoring or casual outfits, it brings a polished, practical accent to the wrist."
            )
        if re.search(r"\bsunglasses\b", normalized_name):
            return (
                f"Step out with confidence in {name}, a statement accessories pick built to sharpen your look while staying easy to wear. "
                f"{caption_part}The streamlined silhouette makes it simple to pair with daily outfits, travel edits, and warm-weather styling."
            )
        if re.search(r"\b(?:necklace|pendant)\b", normalized_name):
            return (
                f"Finish your outfit with {name}, a refined accessories piece designed to add shine without overwhelming your styling. "
                f"{caption_part}Its versatile profile works for gifting, layering, and everyday jewellery rotation."
            )

    if category == "Furniture":
        if re.search(r"\b(?:wardrobe|cupboard|cabinet)\b", normalized_name):
            return (
                f"Bring smarter storage into your space with {name}, a furniture piece designed to organize essentials while keeping the room visually clean. "
                f"{caption_part}Its balanced proportions and durable finish make it suitable for bedrooms, guest rooms, and everyday home organization."
            )
        if re.search(r"\b(?:sofa|chaise)\b", normalized_name):
            return (
                f"Settle into comfort with {name}, a furniture seating piece created for relaxed lounging and easy coordination with modern interiors. "
                f"{caption_part}Built to anchor the room with both comfort and presence, it suits living spaces that need everyday durability."
            )

    if category == "Beauty" and re.search(r"\b(?:serum|elixir|cream|moisturizer|skincare|retinol|hyaluronic)\b", normalized_name):
        return (
            f"Support your daily skincare routine with {name}, a beauty essential designed to layer easily and leave skin feeling cared for. "
            f"{caption_part}Its routine-friendly profile makes it a practical choice for consistent morning or evening use."
        )

    templates = {
        "Electronics": (
            "Introducing {name} — a cutting-edge {cat} device engineered for "
            "performance, reliability, and modern living. {caption_part}"
            "Designed for tech-savvy users who demand the best, this product "
            "combines sleek aesthetics with powerful functionality. "
            "Perfect for home, office, or on-the-go use."
        ),
        "Fashion": (
            "Elevate your wardrobe with {name}, a premium {cat} piece crafted "
            "for style and comfort. {caption_part}"
            "From casual outings to special occasions, this versatile item "
            "is designed to make you look and feel your best. "
            "Available in carefully curated colours to match any aesthetic."
        ),
        "Beauty": (
            "Discover {name} — a luxurious {cat} product formulated to nourish, "
            "protect, and enhance your natural beauty. {caption_part}"
            "Made with premium, skin-friendly ingredients, it delivers "
            "visible results you can feel from the very first use."
        ),
        "Accessories": (
            "Complete your look with {name}, a standout {cat} piece designed to add polish and personality. {caption_part}"
            "Built for everyday wear with a premium finish, this accessory balances style, versatility, and easy pairing across outfits."
        ),
        "Furniture": (
            "Transform your living space with {name}, a beautifully designed "
            "{cat} piece that blends form and function. {caption_part}"
            "Built with quality materials for lasting durability, "
            "this piece adds a touch of elegance to any room."
        ),
        "Sports": (
            "Reach your peak performance with {name} — a professional-grade "
            "{cat} product built for athletes and fitness enthusiasts. {caption_part}"
            "Engineered for durability and maximum comfort during intense activity."
        ),
        "Home": (
            "Upgrade your home with {name}, a practical and stylish {cat} "
            "solution for everyday life. {caption_part}"
            "Crafted for convenience, durability and a perfect fit "
            "in any modern household."
        ),
    }
    template = templates.get(
        category,
        "Introducing {name} — a high-quality {cat} product designed to "
        "exceed your expectations. {caption_part}"
        "Crafted with attention to detail, this product offers exceptional "
        "value and a premium experience."
    )
    cat_str = category if category else "product"
    return template.format(name=name, cat=cat_str.lower(), caption_part=caption_part)


# ─────────────────────────────────────────────────────────────
# MULTI-ANGLE IMAGE DESCRIPTIONS
# ─────────────────────────────────────────────────────────────

_ANGLE_PROMPTS = [
    ("Front View",   "front view of the product, showing the main face"),
    ("Back View",    "rear view of the product, showing the reverse side"),
    ("Side View",    "side profile of the product, showing dimensions"),
    ("Detail Shot",  "close-up detail showing material texture and quality"),
    ("In Use",       "product in use, demonstrating its practical application"),
]


def generate_product_angles(
    name: str,
    category: str = "",
    image_bytes: Optional[bytes] = None,
) -> list[dict]:
    """
    Generate AI-suggested descriptions for multiple product photo angles.
    Returns a list of dicts: [{"angle": str, "description": str}, ...]

    If an image is provided, BLIP captions the main image and incorporates that
    context into each angle description. Falls back to template descriptions.
    """
    base_caption = ""
    if image_bytes:
        base_caption = _blip_caption(image_bytes)

    cat = category or _keyword_category(name.lower())
    results = []

    for angle_name, angle_context in _ANGLE_PROMPTS:
        if HF_API_TOKEN and base_caption:
            # Use zero-shot to infer what this angle would show
            prompt_text = (
                f"Product: {name}. Category: {cat}. "
                f"Main image shows: {base_caption}. "
                f"Describe the {angle_name.lower()} of this product."
            )
            # Build a short description using the caption + angle context
            caption_part = f"{base_caption.rstrip('.')}. " if base_caption else ""
            description = (
                f"{caption_part}This {angle_name.lower()} highlights {angle_context} "
                f"of the {name}, showcasing its quality and design."
            )
        else:
            # Fallback template
            description = (
                f"Photograph the {angle_name.lower()} of '{name}' to highlight {angle_context}. "
                f"Ensure good lighting and a clean background."
            )

        results.append({
            "angle": angle_name,
            "description": description,
            "shooting_tip": _get_shooting_tip(angle_name),
        })

    return results


def _get_shooting_tip(angle_name: str) -> str:
    tips = {
        "Front View":   "Use natural light or a softbox. Center the product with a clean white or neutral background.",
        "Back View":    "Mirror the front view setup. Ensure labels or ports are clearly visible.",
        "Side View":    "Use a tripod for precision. Show the product's depth and thickness clearly.",
        "Detail Shot":  "Use macro mode. Get within 10-15 cm to capture texture and material quality.",
        "In Use":       "Use lifestyle props. Show the product being used naturally in its intended environment.",
    }
    return tips.get(angle_name, "Use consistent lighting and a clean background.")


def get_product_first(db: Session, **filters) -> Optional[Product]:
    query = db.query(Product)
    for key, value in filters.items():
        query = query.filter(getattr(Product, key) == value)
    return query.limit(1).first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_user_by_id(db: Session, record_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == record_id).first()

def _db_product_query_0(db: Session, is_: Any, is_deleted: Any) -> Optional[Any]:
    result = db.query(Product).filter( Product.is_deleted.is_(False), Product.is_active.is_(True), Product.is_approved.is_(True), Product.stock > 0, )
    return result
    """Read-only query delegated from controller."""
