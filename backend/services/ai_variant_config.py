"""
AI-assisted product analysis + variant suggestion for supplier uploads.

Ported from ``Working_API/zozi_ai_upload_session/upload_auto_05.py``:

* ``MasterAttributeDatabase`` (JSON-driven classifier) → :class:`VariantConfig`.
* The variant-matching rules (liquids → volume, solids → weight, mutual
  exclusion, auto-add size for apparel).

The primary path is a **heuristic classifier** that never requires external
services (uses the uploaded filename + the bundled ``zozi_variant_config.json``).
When Ollama (``phi3:mini`` + ``moondream``) is reachable it is used to refine
the result via vision; otherwise we fall back to the heuristic silently.

Copy source of the config asset:
``Working_API/zozi_ai_upload_session/zozi_variant_config.json``
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_CONFIG_PATHS = [
    Path(__file__).resolve().parent.parent / "data" / "zozi_variant_config.json",
    Path("Working_API") / "zozi_ai_upload_session" / "zozi_variant_config.json",
]

_OLLAMA_BASE_URL = "http://localhost:11434"
_OLLAMA_TEXT_MODEL = "phi3:mini"
# qwen2.5 is natively multilingual (strong Arabic) — used for the AR translation
# pass while phi3 handles the fast English structuring.
_OLLAMA_ARABIC_MODEL = "qwen2.5:latest"
_OLLAMA_VISION_MODEL = "moondream"
_OLLAMA_NUM_CTX = 4096
_OLLAMA_TEMPERATURE = 0.1

# VPS-safety flags. Vision (moondream, ~1.7GB, slow on CPU) is OFF by default so
# the analyze endpoint stays fast + light; flip AI_USE_VISION=true on stronger
# boxes. The text model (phi3:mini) is cheap and powers EN/AR copy by default.
AI_USE_VISION = os.environ.get("AI_USE_VISION", "false").lower() == "true"
AI_USE_OLLAMA_TEXT = os.environ.get("AI_USE_OLLAMA_TEXT", "true").lower() == "true"

# ── Canonical category set (must match the frontend CATEGORIES enum) ──────
# The vision/text models freely invent categories ("shoes", "fashion",
# "appliances"…) that don't exist in the supplier form's dropdown. We normalise
# every suggested category back to one of these so the frontend can actually
# select it (otherwise it falls back to "Other").
CANONICAL_CATEGORIES = [
    "Electronics", "Clothing", "Home & Garden", "Sports & Outdoors", "Books",
    "Beauty & Personal Care", "Toys & Games", "Automotive", "Health & Household",
    "Industrial & Scientific", "Other",
]

# ── Smart auto-pricing (ported from upload_auto_05.auto_price) ──────────────
# Base OMR price per detected product_type. The frontend surfaces this as an
# editable default so suppliers don't start from a blank price field.
_PRICE_BY_TYPE = {
    "electronic": 45.0, "clothing": 19.0, "furniture": 85.0, "appliance": 55.0,
    "jewelry": 29.0, "beauty": 15.0, "food_solid": 8.0, "toy": 22.0,
    "automotive": 40.0, "book": 12.0, "sport": 25.0, "plant": 14.0,
    "pet": 16.0, "tool": 30.0, "digital_product": 10.0, "service": 20.0,
    "liquid": 12.0, "accessory": 18.0, "general": 19.0,
}

# Canonical-category → product_type fallback used when no finer type is known.
_CATEGORY_TO_TYPE = {
    "Electronics": "electronic", "Clothing": "clothing",
    "Home & Garden": "furniture", "Sports & Outdoors": "sport",
    "Books": "book", "Beauty & Personal Care": "beauty",
    "Toys & Games": "toy", "Automotive": "automotive",
    "Health & Household": "beauty", "Industrial & Scientific": "tool",
    "Other": "general",
}


def suggest_price(product_type: str, product_name: str, category: str = "") -> Dict[str, float]:
    """Return a suggested OMR price + a soft min/max range.

    Mirrors ``upload_auto_05.auto_price``: a base per type plus a small
    deterministic jitter from the product name hash so similar products get
    stable, plausible prices.
    """
    ptype = product_type or _CATEGORY_TO_TYPE.get(category, "general")
    base = _PRICE_BY_TYPE.get(ptype, _PRICE_BY_TYPE["general"])
    # Deterministic jitter in [-1.00, +9.00) keeps prices stable per product.
    jitter = (abs(hash(product_name or "")) % 100) / 10.0
    suggested = round(base + jitter, 3)
    return {
        "ai_suggested_price": suggested,
        "price_min": round(base * 0.75, 3),
        "price_max": round(base * 1.5, 3),
    }

_CATEGORY_ALIASES: Dict[str, str] = {
    # Clothing & accessories
    "clothing": "Clothing", "apparel": "Clothing", "fashion": "Clothing",
    "shirt": "Clothing", "tshirt": "Clothing", "t-shirt": "Clothing", "dress": "Clothing",
    "lingerie": "Clothing", "shoes": "Clothing", "footwear": "Clothing",
    "sneaker": "Clothing", "sneakers": "Clothing", "shoe": "Clothing",
    "jacket": "Clothing", "pants": "Clothing", "trousers": "Clothing",
    "skirt": "Clothing", "hat": "Clothing", "sock": "Clothing", "socks": "Clothing",
    "bag": "Clothing", "accessory": "Clothing", "accessories": "Clothing",
    "belt": "Clothing", "scarf": "Clothing", "glove": "Clothing", "gloves": "Clothing",
    "jewelry": "Clothing", "jewellery": "Clothing", "watch": "Clothing",
    # Electronics
    "electronics": "Electronics", "electronic": "Electronics", "phone": "Electronics",
    "smartphone": "Electronics", "laptop": "Electronics", "computer": "Electronics",
    "camera": "Electronics", "gadget": "Electronics", "headphone": "Electronics",
    "headphones": "Electronics", "earphone": "Electronics", "earphones": "Electronics",
    "speaker": "Electronics", "tv": "Electronics", "television": "Electronics",
    "tablet": "Electronics", "smartwatch": "Electronics", "console": "Electronics",
    "drone": "Electronics", "charger": "Electronics", "router": "Electronics",
    # Home & Garden
    "home": "Home & Garden", "furniture": "Home & Garden", "kitchen": "Home & Garden",
    "appliance": "Home & Garden", "appliances": "Home & Garden", "garden": "Home & Garden",
    "decor": "Home & Garden", "decoration": "Home & Garden", "bedding": "Home & Garden",
    "lamp": "Home & Garden", "lighting": "Home & Garden", "cookware": "Home & Garden",
    "tableware": "Home & Garden", "storage": "Home & Garden", "rug": "Home & Garden",
    # Sports & Outdoors
    "sports": "Sports & Outdoors", "sport": "Sports & Outdoors",
    "outdoor": "Sports & Outdoors", "outdoors": "Sports & Outdoors",
    "fitness": "Sports & Outdoors", "athletic": "Sports & Outdoors",
    "exercise": "Sports & Outdoors", "cycling": "Sports & Outdoors",
    "camping": "Sports & Outdoors", "yoga": "Sports & Outdoors",
    # Books
    "book": "Books", "books": "Books", "novel": "Books", "textbook": "Books",
    "magazine": "Books", "journal": "Books",
    # Beauty & Personal Care
    "beauty": "Beauty & Personal Care", "cosmetic": "Beauty & Personal Care",
    "cosmetics": "Beauty & Personal Care", "makeup": "Beauty & Personal Care",
    "perfume": "Beauty & Personal Care", "skincare": "Beauty & Personal Care",
    "fragrance": "Beauty & Personal Care", "personal care": "Beauty & Personal Care",
    "haircare": "Beauty & Personal Care",
    # Toys & Games
    "toy": "Toys & Games", "toys": "Toys & Games", "game": "Toys & Games",
    "games": "Toys & Games", "puzzle": "Toys & Games",
    # Automotive
    "automotive": "Automotive", "car": "Automotive", "auto": "Automotive",
    "vehicle": "Automotive", "motorcycle": "Automotive", "tyre": "Automotive",
    "tire": "Automotive", "battery": "Automotive",
    # Health & Household
    "health": "Health & Household", "household": "Health & Household",
    "medical": "Health & Household", "vitamin": "Health & Household",
    "supplement": "Health & Household", "cleaning": "Health & Household",
    "groceries": "Health & Household", "grocery": "Health & Household",
    "food": "Health & Household", "beverage": "Health & Household",
    "baby": "Health & Household", "pet": "Health & Household",
    # Industrial & Scientific
    "industrial": "Industrial & Scientific", "scientific": "Industrial & Scientific",
    "tool": "Industrial & Scientific", "tools": "Industrial & Scientific",
    "machinery": "Industrial & Scientific", "hardware": "Industrial & Scientific",
    # Product-type names (from zozi_variant_config.json product_type_keywords) that
    # need mapping to canonical categories — these are used by _candidate_from_filename.
    # NOTE: do NOT add "general" or "service" here — those are handled directly in
    # normalize_category() so they don't pollute the variant-search terms for "Other".
    "liquid": "Beauty & Personal Care",
    "food_solid": "Health & Household",
    "electronic": "Electronics",
    "appliance": "Home & Garden",
    "beauty": "Beauty & Personal Care",
    "sport": "Sports & Outdoors",
    "plant": "Home & Garden",
    "digital_product": "Electronics",
}

def _canonical_category_terms(canonical: str) -> List[str]:
    """Expand a canonical category to all the alias terms that variant
    ``categories`` fields use (e.g. "Beauty & Personal Care" → ["beauty",
    "cosmetic", "cosmetics", "makeup", …]).

    Variant entries in ``zozi_variant_config.json`` use short tags like
    ``"beauty"`` / ``"cosmetics"``, never the full canonical name.  This helper
    lets ``get_allowed_variants`` match on any alias so the category filter
    actually finds relevant variants.
    """
    terms: List[str] = [canonical.lower()]
    for alias, canon in _CATEGORY_ALIASES.items():
        if canon == canonical:
            a = alias.lower().strip()
            if a and a not in terms:
                terms.append(a)
    return terms


_JUNK_FILENAME_PATTERNS = [
    r'^img_\d+', r'^dsc[n_]?\d+', r'^photo_\d+', r'^pict\d+',
    r'^whatsapp', r'^signal', r'^telegram', r'^screenshot',
    r'^wp_\d+', r'^tmp_', r'^untitled', r'^new_photo',
    r'^camera_\d+', r'^image_\d+', r'^pic_\d+',
]


def _is_junk_filename(filename: str) -> bool:
    """Check if the filename is a camera/auto-generated name with no semantic
    content. Returns True for names like IMG_1234, DSC_001, photo_2024, etc."""
    base = (filename or "").rsplit(".", 1)[0].strip().lower()
    if not base or len(base) <= 2:
        return True
    for pat in _JUNK_FILENAME_PATTERNS:
        if re.search(pat, base):
            return True
    # If the name is purely numeric or a single letter + numbers, it's junk.
    if re.match(r'^[a-z]?\d+$', base):
        return True
    return False


_CV_CATEGORY_CLUES = {
    "Clothing": {
        "keywords": ["apparel", "cloth", "fashion", "shirt", "dress", "shoe", "jacket", "pant"],
        "min_edge_density": 0.2,
        "max_single_color_dominance": 0.7,
    },
    "Electronics": {
        "keywords": ["electronic", "phone", "laptop", "computer", "camera", "gadget"],
        "min_edge_density": 0.3,
        "max_single_color_dominance": 0.85,
    },
    "Beauty & Personal Care": {
        "keywords": ["beauty", "cosmetic", "perfume", "skincare", "makeup"],
        "min_edge_density": 0.1,
        "max_single_color_dominance": 0.6,
    },
}

# Singular-ish noun used to build a fallback product name when vision can't
# name the item (e.g. "Black Sneakers" from colours + a shoes-derived noun).
_CATEGORY_NOUN: Dict[str, str] = {
    "Electronics": "Electronics", "Clothing": "Clothing",
    "Home & Garden": "Home Product", "Sports & Outdoors": "Sports Gear",
    "Books": "Book", "Beauty & Personal Care": "Beauty Product",
    "Toys & Games": "Toy", "Automotive": "Auto Part",
    "Health & Household": "Product", "Industrial & Scientific": "Tool",
    "Other": "Product",
}


def normalize_category(raw: str) -> str:
    """Map a free-form vision category onto the canonical frontend set."""
    if not raw:
        return "Other"
    r = raw.strip().lower()
    if r in ("general", "service"):
        return "Other"
    for c in CANONICAL_CATEGORIES:
        if c.lower() == r:
            return c
    if r in _CATEGORY_ALIASES:
        return _CATEGORY_ALIASES[r]
    # Word-boundary / substring alias match.
    for alias, canon in _CATEGORY_ALIASES.items():
        if alias and (alias in r or r in alias):
            return canon
    for c in CANONICAL_CATEGORIES:
        if c.lower() in r or r in c.lower():
            return c
    return "Other"


def _build_fallback_name(category: str, color_list: List[str], raw_category_hint: str) -> str:
    """Build a sensible product name from detected signals when vision can't
    name the item — never fall back to the (often junk) upload filename."""
    hint = (raw_category_hint or "").strip().lower()
    noun = _PRODUCT_NOUN_HINTS.get(hint) or _CATEGORY_NOUN.get(category, "Product")
    parts = [c.title() for c in (color_list or [])[:2]]
    name = " ".join(parts + [noun]).strip()
    return name or "Product"


_PRODUCT_NOUN_HINTS: Dict[str, str] = {
    "shoes": "Sneakers", "sneaker": "Sneakers", "sneakers": "Sneakers",
    "footwear": "Footwear", "shoe": "Shoes", "watch": "Watch", "watches": "Watches",
    "tshirt": "T-Shirt", "t-shirt": "T-Shirt", "shirt": "Shirt", "dress": "Dress",
    "jacket": "Jacket", "pants": "Pants", "trousers": "Trousers", "skirt": "Skirt",
    "hat": "Hat", "bag": "Bag", "socks": "Socks", "scarf": "Scarf",
    "phone": "Phone", "smartphone": "Phone", "laptop": "Laptop", "computer": "Computer",
    "camera": "Camera", "headphone": "Headphones", "headphones": "Headphones",
    "speaker": "Speaker", "tablet": "Tablet", "perfume": "Perfume",
    "cosmetic": "Cosmetic", "makeup": "Makeup", "book": "Book", "books": "Book",
    "toy": "Toy", "game": "Game", "car": "Car Part", "tool": "Tool",
}


def _load_config() -> Dict[str, Any]:
    for path in _CONFIG_PATHS:
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    cfg = json.load(fh)
                logger.info("ai_variant_config: loaded %s", path)
                return cfg
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning("ai_variant_config: failed to load %s (%s)", path, exc)
    logger.warning("ai_variant_config: no config asset found, using empty defaults")
    return {}


class VariantConfig:
    """JSON-driven variant database, mirroring ``MasterAttributeDatabase``."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config if config is not None else _load_config()

    # ── helpers ──────────────────────────────────────────────────────
    def get_variants(self) -> Dict[str, Any]:
        return self.config.get("variants", {})

    def get_product_type_keywords(self) -> Dict[str, List[str]]:
        keywords = self.config.get("product_type_keywords", {})
        if "clothing" in keywords:
            for item in ["lingerie", "bralette", "bra", "underwear", "panties"]:
                if item not in keywords["clothing"]:
                    keywords["clothing"].append(item)
        return keywords

    def get_category_fallbacks(self) -> Dict[str, List[str]]:
        return self.config.get("category_fallbacks", {})

    def get_ai_rules(self) -> Dict[str, Any]:
        return self.config.get("ai_rules", {})

    def get_rules_for_product_type(self, product_type: str) -> Dict[str, Any]:
        """Return the include/exclude rule block for a classified product type."""
        return self.get_ai_rules().get(f"{product_type}_rules", {})

    def get_variant_info(self, variant_key: str) -> Dict[str, Any]:
        return self.get_variants().get(variant_key, {})

    def get_mutually_exclusive(self, variant_key: str) -> List[str]:
        return self.get_variant_info(variant_key).get("mutually_exclusive_with", [])

    # ── classifier ───────────────────────────────────────────────────
    def classify_product_type(self, product_name: str, category: str, subcategory: str) -> str:
        text = f"{product_name} {category} {subcategory}".lower()
        keywords = self.get_product_type_keywords()
        for product_type, type_keywords in keywords.items():
            if any(kw in text for kw in type_keywords):
                return product_type
        category_lower = category.lower()
        fallbacks = self.get_category_fallbacks()
        pairs = [
            ("apparel_keywords", "clothing"),
            ("electronics_keywords", "electronic"),
            ("furniture_keywords", "furniture"),
            ("home_keywords", "appliance"),
            ("jewelry_keywords", "jewelry"),
            ("beauty_keywords", "beauty"),
            ("groceries_keywords", "food_solid"),
            ("toys_keywords", "toy"),
            ("books_keywords", "book"),
            ("automotive_keywords", "automotive"),
        ]
        for kw_key, ptype in pairs:
            if any(kw in category_lower for kw in fallbacks.get(kw_key, [])):
                return ptype
        return "general"

    def get_allowed_variants(self, category: str, subcategory: str) -> List[str]:
        category_lower = category.lower().strip()
        subcategory_lower = subcategory.lower().strip()
        variants = self.get_variants()

        # Expand the canonical category to all its alias terms so we can match
        # against variant categories that use short tags (e.g. "beauty" instead
        # of "Beauty & Personal Care").
        category_terms = _canonical_category_terms(category)

        allowed: List[str] = []
        # Strategy 1: exact match on ANY category alias term.
        # Subcategory is supplemental only — never the sole filter.
        for variant_key, variant_data in variants.items():
            vcats = variant_data.get("categories", [])
            if any(ct in vcats for ct in category_terms):
                allowed.append(variant_key)
        if subcategory_lower and allowed:
            for variant_key, variant_data in variants.items():
                if subcategory_lower in variant_data.get("categories", []):
                    if variant_key not in allowed:
                        allowed.append(variant_key)
        # Strategy 2: partial match — same order: category terms then subcategory.
        if not allowed:
            for variant_key, variant_data in variants.items():
                for cat in variant_data.get("categories", []):
                    if not cat:
                        continue
                    if any(category_lower and (ct in cat or cat in ct) for ct in category_terms):
                        if variant_key not in allowed:
                            allowed.append(variant_key)
            if subcategory_lower and not allowed:
                for variant_key, variant_data in variants.items():
                    for cat in variant_data.get("categories", []):
                        if not cat:
                            continue
                        if subcategory_lower and (subcategory_lower in cat or cat in subcategory_lower):
                            if variant_key not in allowed:
                                allowed.append(variant_key)
        # Strategy 3: keyword-based fallback
        if not allowed:
            fallbacks = self.get_category_fallbacks()
            for kw_key, keys in [
                ("apparel_keywords", ["color", "size", "material", "pattern", "gender"]),
                ("electronics_keywords", ["color", "storage", "ram", "model", "screen_size"]),
                ("jewelry_keywords", ["color", "material", "plating", "size"]),
                ("home_keywords", ["color", "material", "dimensions", "capacity"]),
                ("beauty_keywords", ["color", "volume", "weight", "scent", "skin_type"]),
                ("groceries_keywords", ["flavor", "weight", "volume"]),
                ("toys_keywords", ["color", "size", "age_group"]),
                ("automotive_keywords", ["color", "car_fitment", "vehicle_type", "year"]),
            ]:
                if any(kw in ct or kw in subcategory_lower for ct in category_terms for kw in fallbacks.get(kw_key, [])):
                    allowed = keys
                    break
        # Strategy 4: ultimate fallback — for "Other" or unknown categories,
        # return a useful default set instead of just ["color"] so suppliers
        # have a starting point for their variant matrix.
        if not allowed:
            if category_lower in ("other", "", "general"):
                allowed = ["color", "size", "material"]
            else:
                allowed = ["color"]
        return allowed

    def extract_variant_options(self, variant_key: str) -> List[str]:
        """Pull example option values from the variant's prompt (e.g., parentheses)."""
        info = self.get_variant_info(variant_key)
        prompt = info.get("prompt", "")
        match = re.search(r"\(([^()]*)\)", prompt)
        if not match:
            return []
        inner = match.group(1)
        if "e.g." in inner:
            inner = inner.split("e.g.", 1)[1]
        parts = [p.strip() for p in re.split(r"[,\n]| or ", inner) if p.strip()]
        cleaned: List[str] = []
        for p in parts:
            p = p.strip(" .")
            if p and p.lower() not in ("etc", "e.g", "eg"):
                cleaned.append(p)
        return cleaned[:12]


# ── heuristic text extraction from filename ───────────────────────────

_COLOR_NAMES = {
    "black": (0, 0, 0), "white": (255, 255, 255), "red": (200, 30, 30),
    "green": (30, 160, 60), "blue": (40, 80, 200), "yellow": (230, 200, 40),
    "orange": (230, 130, 30), "purple": (130, 50, 180), "pink": (230, 120, 170),
    "brown": (120, 80, 40), "grey": (130, 130, 130), "gray": (130, 130, 130),
    "silver": (190, 190, 195), "gold": (210, 170, 40), "beige": (210, 195, 160),
    "navy": (20, 30, 80), "olive": (120, 120, 50), "maroon": (110, 20, 40),
    "teal": (20, 140, 140),
}


def _detect_colors_from_filename(filename: str) -> List[str]:
    name = (filename or "").lower()
    found = [c for c in _COLOR_NAMES if c in name]
    return found


def _nearest_color_name(r: int, g: int, b: int) -> Optional[str]:
    """Map an RGB triple to the closest named colour in ``_COLOR_NAMES``.

    Returns ``None`` when no named colour is within a reasonable distance
    (avoids mislabeling unusual shades)."""
    best: Optional[str] = None
    best_d = 1e9
    for name, (cr, cg, cb) in _COLOR_NAMES.items():
        d = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if d < best_d:
            best_d = d
            best = name
    return best if best_d < 14000 else None


def _analyze_photo_cv(image_bytes: bytes) -> Dict[str, Any]:
    """Lightweight computer-vision analysis of the actual photo pixels.

    Runs in milliseconds using pure PIL + numpy (no GPU, no external service)
    so it can enrich the *instant* analyse response with real, photo-derived
    signals — most importantly the dominant colours, which the heuristic path
    previously guessed from the filename only.

    Returns:

    * ``dominant_colors`` — up to 5 named colours, most frequent first.
    * ``background`` — ``"simple"`` (solid/flat) or ``"busy"``.
    * ``bg_complexity`` — 0..1 edge-density score.
    * ``suggested_bg_preset`` — a recommended background-removal preset, or
      ``None`` when the backdrop already looks clean.
    """
    try:
        from PIL import Image as _PILImage
        import numpy as np
        im = _PILImage.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as exc:  # noqa: BLE001
        logger.info("ai_variant_config: CV analysis skipped (%s)", exc)
        return {"dominant_colors": [], "background": "unknown", "bg_complexity": 0.0,
                "suggested_bg_preset": None}

    try:
        small = im.resize((96, 96))
        arr = np.asarray(small, dtype=np.float32).reshape(-1, 3)
        # Quantize to 5-bit buckets to group visually similar shades, then
        # rank buckets by pixel frequency.
        buckets = (arr / 8).astype(np.int32)
        keys, inv = np.unique(buckets, axis=0, return_inverse=True)
        counts = np.bincount(inv)
        order = np.argsort(counts)[::-1]

        named: List[str] = []
        for idx in order[:10]:
            rgb = (keys[idx] * 8).astype(np.int32)
            name = _nearest_color_name(int(rgb[0]), int(rgb[1]), int(rgb[2]))
            if name:
                named.append(name)
            if len(named) >= 5:
                break
        seen: set = set()
        dominant: List[str] = []
        for n in named:
            if n not in seen:
                seen.add(n)
                dominant.append(n)

        # Background complexity via gradient magnitude (edge density).
        gray = np.asarray(small.convert("L"), dtype=np.float32)
        gx = float(np.abs(gray[:, 1:] - gray[:, :-1]).mean())
        gy = float(np.abs(gray[1:, :] - gray[:-1, :]).mean())
        complexity = float(min(1.0, (gx + gy) / 80.0))

        top_share = float(counts[order[0]] / counts.sum()) if counts.sum() else 0.0
        if complexity > 0.25 and top_share < 0.6:
            suggested_bg: Optional[str] = "birefnet_production"
        elif complexity > 0.15:
            suggested_bg = "clean_commercial"
        else:
            suggested_bg = None

        # CV-based category hint: use edge density + color distribution to
        # guess the product type when the filename provides no semantic clues.
        # High edge density + moderate color diversity → likely Clothing.
        # Very high single-color dominance + low complexity → Beauty/Personal Care.
        # Moderate edges + moderate diversity → Home & Garden or Sports.
        top_share_val = float(counts[order[0]] / counts.sum()) if counts.sum() else 0.0
        cv_cat_hint = ""
        num_colors = len([n for n in named if n]) if named else 0
        if complexity > 0.2 and top_share_val < 0.7 and num_colors >= 3:
            cv_cat_hint = "Clothing"
        elif complexity > 0.25 and (top_share_val > 0.7 or num_colors <= 2):
            cv_cat_hint = "Electronics"
        elif complexity < 0.2 and top_share_val > 0.65 and num_colors <= 3:
            cv_cat_hint = "Beauty & Personal Care"
        elif complexity > 0.12 and top_share_val < 0.8 and num_colors >= 2:
            cv_cat_hint = "Home & Garden"

        return {
            "dominant_colors": dominant,
            "background": "simple" if complexity < 0.15 else "busy",
            "bg_complexity": round(complexity, 3),
            "suggested_bg_preset": suggested_bg,
            "cv_category_hint": cv_cat_hint,
        }
    except Exception as exc:  # noqa: BLE001
        logger.info("ai_variant_config: CV analysis failed (%s)", exc)
        return {"dominant_colors": [], "background": "unknown", "bg_complexity": 0.0,
                "suggested_bg_preset": None, "cv_category_hint": ""}


def _candidate_from_filename(filename: str) -> Dict[str, str]:
    """Guess category/subcategory/product-name hint from the filename.

    Returns empty strings for camera/auto-generated filenames (IMG_1234, etc.)
    so the heuristic path falls through to CV-based signals instead."""
    if _is_junk_filename(filename):
        return {"category": "", "subcategory": "", "product_name": ""}
    base = (filename or "").rsplit(".", 1)[0]
    words = re.split(r"[^a-z0-9]+", base.lower())
    text = " ".join(words)
    cfg = _CONFIG
    keywords = cfg.get_product_type_keywords()
    category = ""
    for ptype, kws in keywords.items():
        if any(kw in text for kw in kws):
            category = ptype
            break
    if not category:
        fallbacks = cfg.get_category_fallbacks()
        for kw_key, ptype in [
            ("apparel_keywords", "Apparel"), ("electronics_keywords", "Electronics"),
            ("jewelry_keywords", "Jewelry"), ("home_keywords", "Home"),
            ("beauty_keywords", "Beauty"), ("groceries_keywords", "Groceries"),
            ("toys_keywords", "Toys"), ("automotive_keywords", "Automotive"),
            ("books_keywords", "Books"), ("furniture_keywords", "Furniture"),
        ]:
            if any(kw in text for kw in fallbacks.get(kw_key, [])):
                category = ptype
                break
    subcategory = ""
    for word in words:
        if word and word != category and len(word) > 2:
            subcategory = word.title()
            break
    product_name = base.replace("_", " ").replace("-", " ").strip().title() or "Product"
    return {"category": category, "subcategory": subcategory, "product_name": product_name}


# ── optional Ollama vision refinement ─────────────────────────────────

async def _ollama_chat(model: str, content: str, images: Optional[List[str]] = None,
                       num_predict: int = 600, temperature: float = 0.2,
                       timeout: float = 90.0) -> Optional[str]:
    """Call Ollama via its OpenAI-compatible /v1/chat/completions endpoint.

    This endpoint is what actually supports vision on this box (moondream
    returns empty/garbage through the native /api/chat images field, but works
    perfectly through image_url here). keep_alive pins the model so repeated
    calls don't pay the 10s reload cost.
    """
    try:
        import httpx
    except ImportError:
        return None
    if images:
        content_msg: Any = [
            {"type": "text", "text": content},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{images[0]}"}},
        ]
    else:
        content_msg = content
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content_msg}],
        "temperature": temperature,
        "max_tokens": num_predict,
        "keep_alive": "5m",
    }
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(f"{_OLLAMA_BASE_URL}/v1/chat/completions", json=payload)
            if resp.status_code != 200:
                logger.info("ai_variant_config: Ollama %s responded %s", model, resp.status_code)
                return None
            return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:  # noqa: BLE001
        logger.info("ai_variant_config: Ollama %s unavailable (%s)", model, exc)
        return None


def _extract_json(content: str) -> Optional[Dict[str, Any]]:
    if not content:
        return None
    txt = content.strip()
    if "```" in txt:
        txt = re.sub(r"```[a-zA-Z]*\n?", "", txt)
        txt = txt.rstrip("`").strip()
    m = re.search(r"\{[\s\S]*\}", txt)
    if not m:
        return None
    raw = m.group()
    try:
        return json.loads(raw, strict=False)
    except json.JSONDecodeError:
        pass
    # Tolerant repair for small-model JSON quirks.
    s = raw
    s = re.sub(r"(?<!\\)'", '"', s)
    s = re.sub(r"\bNone\b", "null", s)
    s = re.sub(r",\s*}", "}", s)
    s = re.sub(r",\s*]", "]", s)
    try:
        return json.loads(s, strict=False)
    except json.JSONDecodeError:
        return None


async def _try_ollama_vision(image_bytes: bytes, product_name_hint: str) -> Optional[str]:
    """Best-effort vision analysis through Ollama (moondream).

    moondream reliably returns natural-language prose (not strict JSON), so we
    ask for a short factual description and let the text model structure it.
    Returns the description string, or None if vision is unavailable.
    """
    try:
        import base64
    except ImportError:
        return None
    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        vision_prompt = (
            "You are analysing a marketplace product photo. Focus ONLY on the main "
            "product being sold. If a person or model is shown, describe the product "
            "they are wearing or holding — not the person. In 2-4 short factual "
            "sentences state: the product type/name, any brand visible on the item or "
            "its packaging, the category, the colour(s), the material, and whether it "
            "looks new or used. Do not invent details that are not visible."
        )
        content = await _ollama_chat(_OLLAMA_VISION_MODEL, vision_prompt, images=[b64],
                                     num_predict=200, temperature=0.2)
        return content.strip() if content else None
    except Exception as exc:  # noqa: BLE001
        logger.info("ai_variant_config: Ollama vision unavailable (%s)", exc)
        return None


async def _structure_with_text(description: str, fallback_name: str,
                               category: str, subcategory: str,
                               replace_null_product_name: bool = True) -> Optional[Dict[str, Any]]:
    """Use phi3:mini to turn a vision description into structured product data.

    Returns a dict with name/category/subcategory/attributes + EN/AR copy, or
    None if the text model is unavailable / unparseable.
    """
    # Call 1 — English structure only (small, fast on CPU).
    canonical_list = ", ".join(CANONICAL_CATEGORIES)
    en_prompt = (
        "You are a product data specialist for an Oman/GCC marketplace (ZOZI).\n"
        f"IMAGE DESCRIPTION:\n{description}\n\n"
        f"Choose the category from EXACTLY this list: {canonical_list}.\n"
        "Reply ONLY with valid JSON (double quotes, no markdown, no commentary).\n"
        "RULES:\n"
        "- product_name, english_title, english_description and suggested_tags are "
        "REQUIRED — never use null for them.\n"
        "- english_description must be 2-3 persuasive sentences.\n"
        "- suggested_tags must be 8-12 lowercase SEO search tags.\n"
        "- suggested_variants: up to 4 most relevant SELLABLE variant axes, each with "
        'a "label" (display name) and 3-6 "options".\n'
        "- Use null only for brand / uncertain single attributes. Never invent a brand.\n"
        "{\n"
        '  "product_name": str,\n'
        '  "category": str (one of the list above),\n'
        '  "subcategory": str or null,\n'
        '  "brand": str or null,\n'
        '  "detected_attributes": {"color": str or null, "material": str or null, '
        '"condition": str or null, "style": str or null},\n'
        '  "english_title": str (max 80 chars, SEO),\n'
        '  "english_description": str (2-3 sentences, persuasive),\n'
        '  "bullet_points_en": [3 short strings],\n'
        '  "suggested_tags": [8-12 lowercase SEO search tags as strings],\n'
        '  "suggested_variants": [{"axis": str ("color"|"size"|"material"|"pattern"|'
        '"storage"|"volume"|...), "label": str (display name), "options": [3-6 example '
        "values as strings]}] (max 4 most relevant sellable variant axes)\n"
        "}"
    )
    content = await _ollama_chat(_OLLAMA_TEXT_MODEL, en_prompt, num_predict=300, temperature=0.3)
    if not content:
        return None
    data = _extract_json(content)
    if not isinstance(data, dict):
        return None
    data.setdefault("detected_attributes", {})
    if not data.get("product_name") and replace_null_product_name:
        data["product_name"] = fallback_name

    # Call 2 — Arabic translation of the finished EN copy (separate small call so
    # the RTL/token-heavy generation never blows the single-request budget).
    en_title = data.get("english_title") or data.get("product_name") or fallback_name
    en_desc = data.get("english_description") or ""
    en_bullets = data.get("bullet_points_en") or []
    ar_prompt = (
        "Translate this product listing into natural marketing Arabic.\n"
        f"TITLE: {en_title}\n"
        f"DESCRIPTION: {en_desc}\n"
        f"BULLETS: {' | '.join(str(b) for b in en_bullets)}\n\n"
        "Reply ONLY with valid JSON (double quotes, no markdown):\n"
        "{\n"
        '  "arabic_title": str,\n'
        '  "arabic_description": str,\n'
        '  "bullet_points_ar": [str]\n'
        "}"
    )
    ar_content = await _ollama_chat(_OLLAMA_ARABIC_MODEL, ar_prompt, num_predict=350,
                                    temperature=0.3, timeout=180.0)
    ar_data = _extract_json(ar_content) if ar_content else None
    if not isinstance(ar_data, dict):
        # qwen sometimes returns Arabic inside markdown or with stray prose —
        # scrape the individual fields rather than dropping the whole translation.
        ar_data = _scrape_arabic_fields(ar_content or "")
    if isinstance(ar_data, dict):
        data["arabic_title"] = ar_data.get("arabic_title", "") or ""
        data["arabic_description"] = ar_data.get("arabic_description", "") or ""
        data["bullet_points_ar"] = ar_data.get("bullet_points_ar") or []
    else:
        data.setdefault("arabic_title", "")
        data.setdefault("arabic_description", "")
        data.setdefault("bullet_points_ar", [])
    return data


def _scrape_arabic_fields(text: str) -> Dict[str, Any]:
    """Best-effort extraction of the Arabic title/description when the model
    wraps its JSON in markdown or adds commentary."""
    if not text:
        return {}
    out: Dict[str, Any] = {}
    for key in ("arabic_title", "arabic_description"):
        m = re.search(rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.UNICODE)
        if m:
            out[key] = m.group(1).encode().decode("unicode_escape", "ignore")
    m = re.search(r'"bullet_points_ar"\s*:\s*\[(.*?)\]', text, re.DOTALL | re.UNICODE)
    if m:
        items = re.findall(r'"((?:[^"\\]|\\.)*)"', m.group(1), re.UNICODE)
        out["bullet_points_ar"] = [i.encode().decode("unicode_escape", "ignore") for i in items]
    return out


def _generate_description(
    product_name: str,
    category: str,
    subcategory: str,
    color_list: List[str],
    material_list: Optional[List[str]],
    brand: str = "",
) -> str:
    """Build a persuasive, SEO-friendly product description from detected data."""
    color_txt = ", ".join(color_list) if color_list else ""
    material_txt = ", ".join(material_list) if material_list else ""
    parts = []
    display_name = f"{brand} {product_name}".strip() if brand and brand.lower() not in product_name.lower() else product_name

    # Category-specific description templates for better relevance.
    cat_lower = category.lower()
    if "cloth" in cat_lower or "fashion" in cat_lower or "apparel" in cat_lower:
        lead = f"Step up your style with the {display_name}"
        if color_txt:
            lead += f" in {color_txt}"
        lead += f" — a premium {category} piece"
        if subcategory and subcategory.lower() not in ("general", "other"):
            lead += f" from our {subcategory} collection"
        lead += ". Designed to keep you looking sharp and feeling comfortable all day."
        parts.append(lead)
        feature = "Made from quality materials with careful attention to detail"
        if material_txt:
            feature += f", featuring {material_txt}"
        feature += ". The versatile design pairs easily with your existing wardrobe for endless styling options."
        parts.append(feature)
    elif "electron" in cat_lower:
        lead = f"Experience cutting-edge technology with the {display_name}"
        if color_txt:
            lead += f" in {color_txt}"
        lead += f" — a top-tier {category} device"
        if subcategory and subcategory.lower() not in ("general", "other"):
            lead += f" in the {subcategory} lineup"
        lead += ". Engineered for performance and built to last."
        parts.append(lead)
        feature = "Packed with the latest features and smart technology to enhance your daily life"
        if material_txt:
            feature += f", constructed from {material_txt}"
        feature += ". Reliable, efficient, and designed with the modern user in mind."
        parts.append(feature)
    elif "beauty" in cat_lower or "personal care" in cat_lower:
        lead = f"Treat yourself with the {display_name}"
        if color_txt:
            lead += f" in {color_txt}"
        lead += f" — a premium {category} essential"
        if subcategory and subcategory.lower() not in ("general", "other"):
            lead += f" from our {subcategory} range"
        lead += ". Formulated to help you look and feel your best."
        parts.append(lead)
        feature = "Developed with care using quality ingredients and thoughtful design"
        if material_txt:
            feature += f", enriched with {material_txt}"
        feature += ". A wonderful addition to your daily self-care routine."
        parts.append(feature)
    else:
        lead = f"Discover the {display_name}"
        if color_txt:
            lead += f" in {color_txt}"
        lead += f" — a quality {category} product"
        if subcategory and subcategory.lower() not in ("general", "other"):
            lead += f" in the {subcategory} range"
        lead += "."
        parts.append(lead)
        feature = "Crafted for everyday use with a focus on quality and durability"
        if material_txt:
            feature += f", made from {material_txt}"
        feature += ". Designed to deliver reliable performance that fits seamlessly into your lifestyle."
        parts.append(feature)

    parts.append(
        "Order now for fast GCC delivery, secure checkout, and Zozi's trusted supplier guarantee. "
        "Perfect as a gift or a personal upgrade."
    )
    return " ".join(parts)


def _generate_tags(
    product_name: str,
    category: str,
    subcategory: str,
    color_list: List[str],
    material_list: Optional[List[str]],
    brand: str = "",
) -> List[str]:
    """Generate 10-15 highly relevant SEO search tags from detected data."""
    # Tokens that come from upload filenames (IMG_1234, sample_*, DSC…) and add
    # no SEO value — strip them so tags stay meaningful.
    _JUNK_TOKENS = {
        "img", "sample", "photo", "image", "picture", "dsc", "wp", "screenshot",
        "tmp", "untitled", "product", "new", "copy", "edit", "final", "raw",
    }
    raw = []
    if brand:
        raw.append(brand.lower())
    for token in re.split(r"[^a-z0-9]+", (product_name or "").lower()):
        if len(token) > 2 and token not in ("the", "and", "for", "with") and not token.isdigit():
            if token in _JUNK_TOKENS:
                continue
            raw.append(token)
    # Don't add "other" as a tag — it adds no SEO value.
    cat_lower = category.lower()
    if cat_lower and cat_lower != "other":
        raw.append(cat_lower)
    # For "Other" category products, add a useful generic fallback tag.
    if cat_lower == "other":
        raw.extend(["accessories", "merchandise"])
    if subcategory and subcategory.lower() not in ("general", "other"):
        raw.append(subcategory.lower())
    for c in color_list:
        raw.append(c.lower())
    if material_list:
        for m in material_list:
            raw.append(m.lower())
    # Common GCC / e-commerce qualifiers — avoid "new" as it conflicts with product/new.
    raw.extend(["zozi", "gcc", "online", "shopping", "fast delivery", "premium"])
    # De-dupe while preserving order
    seen = set()
    tags: List[str] = []
    for t in raw:
        if t and t not in seen:
            seen.add(t)
            tags.append(t)
        if len(tags) >= 15:
            break
    return tags[:15]


async def _try_ollama_text(product_name: str, category: str, color_list: List[str],
                           subcategory: str = "") -> Optional[Dict[str, Any]]:
    """Backwards-compatible alias — wraps ``_structure_with_text`` for callers
    that only have a name (no vision prose). Falls back to a name-only prompt."""
    prompt = (
        f"Product: {product_name} (category: {category}"
        f"{('/ ' + subcategory) if subcategory and subcategory.lower() != 'general' else ''}"
        f"{', color: ' + ', '.join(color_list) if color_list else ''}).\n"
        "Reply ONLY with valid JSON: "
        '{"english_title": str, "english_description": str, '
        '"arabic_title": str, "arabic_description": str, '
        '"bullet_points_en": [str], "bullet_points_ar": [str]}'
    )
    content = await _ollama_chat(_OLLAMA_TEXT_MODEL, prompt, num_predict=600, temperature=0.3)
    if not content:
        return None
    data = _extract_json(content)
    return data if isinstance(data, dict) else None


def _apply_ai_rules(
    allowed: List[str], product_type: str, cfg: "VariantConfig"
) -> Dict[str, Any]:
    """
    Apply the config's ``ai_rules`` include/exclude intelligence for a product
    type (e.g. liquids → volume not weight, solids → weight not volume,
    furniture → dimensions not size, clothing → size not dimensions).

    Returns the adjusted variant list plus the set of keys the rules *force in*
    so downstream refinement won't strip them as metadata.
    """
    rules = cfg.get_rules_for_product_type(product_type)
    if not rules:
        return {"allowed": allowed, "forced": set()}

    result = list(allowed)
    for key in rules.get("exclude", []):
        while key in result:
            result.remove(key)

    variants = cfg.get_variants()
    forced: set = set()
    for key in rules.get("include", []):
        if key in variants:
            forced.add(key)
            if key not in result:
                result.append(key)
    return {"allowed": result, "forced": forced}


def _apply_mutual_exclusion(variants: List[str], cfg: "VariantConfig") -> List[str]:
    result = list(variants)
    for variant in list(variants):
        if variant in result:
            for exclusive in cfg.get_mutually_exclusive(variant):
                if exclusive in result:
                    result.remove(exclusive)
    return result


async def analyze_product_image(
    image_bytes: bytes, filename: str = "", generate_copy: bool = True,
    use_vision: Optional[bool] = None,
) -> Dict[str, Any]:
    """
    Analyze an uploaded product image and suggest category + variants.

    Returns the JSON contract documented in the enhancement plan.

    ``generate_copy`` controls the slow (~60-90s CPU) LLM copy generation:
      - True  → full EN/AR marketing copy via Ollama (use in background jobs).
      - False → instant heuristic-only result (use for the synchronous request).

    ``use_vision`` overrides the ``AI_USE_VISION`` env default for this call:
      - None  → follow the env flag (default off for VPS safety).
      - True  → run moondream vision so the product is detected from the image
                itself (used by the background copy job so real detection never
                blocks the interactive request).
      - False → force vision off regardless of env.
    """
    global _CONFIG
    cfg = _CONFIG

    candidate = _candidate_from_filename(filename)

    # Real, photo-derived signals (colours, background complexity). Cheap + local.
    photo_cv = _analyze_photo_cv(image_bytes)

    vision_enabled = AI_USE_VISION if use_vision is None else use_vision

    # Best-effort Ollama vision → text structuring (heuristic fallback if absent).
    # Vision is gated (heavy on CPU) — see AI_USE_VISION / the use_vision override.
    vision_prose = None
    structured: Optional[Dict[str, Any]] = None
    if generate_copy and vision_enabled:
        vision_prose = await _try_ollama_vision(image_bytes, candidate["product_name"])
        if vision_prose:
            structured = await _structure_with_text(
                vision_prose, candidate["product_name"],
                candidate["category"], candidate["subcategory"],
                replace_null_product_name=False,
            )

    # Text-only fast path: no image understanding, but still produce EN/AR
    # marketing copy from the filename-derived candidate (cheap phi3 call).
    if generate_copy and not structured and AI_USE_OLLAMA_TEXT:
        seed = (
            f"Product name: {candidate['product_name']}. "
            f"Category: {candidate['category'] or 'General'}. "
            f"Subcategory: {candidate['subcategory'] or 'General'}."
        )
        structured = await _structure_with_text(
            seed, candidate["product_name"],
            candidate["category"], candidate["subcategory"],
        )

    if structured:
        # Name: prefer the vision-derived name; never fall back to the upload
        # filename (usually junk like "IMG_1234" / "sample_sneaker"). Build a
        # sensible name from detected colours + category instead.
        raw_cat = structured.get("category") or candidate["category"]
        product_name = structured.get("product_name") or ""
        product_name = product_name.strip() if isinstance(product_name, str) else ""
        if not product_name:
            product_name = _build_fallback_name(
                normalize_category(raw_cat), photo_cv.get("dominant_colors", []), raw_cat)
        category = normalize_category(raw_cat)
        # Subcategory: only keep a meaningful vision-derived value; drop filename
        # junk ("Sample") and generic placeholders.
        subc = structured.get("subcategory") or ""
        subc = subc.strip() if isinstance(subc, str) else ""
        subcategory = subc if subc and subc.lower() not in ("general", "sample") else ""
        detected = structured.get("detected_attributes") or {}
        brand = structured.get("brand") or ""
        ollama_content = structured
    else:
        # When the filename provides no semantic clues (camera/auto-generated),
        # use CV-derived signals as fallback: category hints from edge/color
        # analysis + product name from dominant colours + category noun.
        cv_cat_hint = photo_cv.get("cv_category_hint", "")
        cat_from_cv = normalize_category(cv_cat_hint or candidate["category"]) or "Other"
        if not candidate["product_name"]:
            product_name = _build_fallback_name(
                cat_from_cv, photo_cv.get("dominant_colors", []),
                cv_cat_hint or candidate["category"],
            )
        else:
            product_name = candidate["product_name"]
        category = cat_from_cv
        # Preserve the filename-derived subcategory (e.g. "Perfume Bottle" → "Bottle")
        # when it's a meaningful word, not a generic placeholder.
        cand_sub = (candidate.get("subcategory") or "").strip()
        subcategory = cand_sub if cand_sub and cand_sub.lower() not in ("general", "sample", "product") else ""
        detected = {}
        brand = ""
        ollama_content = None

    # Normalise brand: models sometimes return "unknown"/"n/a"/"none" as strings.
    if isinstance(brand, str):
        brand = brand.strip()
        if brand.lower() in ("", "unknown", "n/a", "na", "none", "null", "generic", "no brand", "unbranded"):
            brand = ""
    else:
        brand = ""

    category = normalize_category(category or "Other")

    # Color detection: prefer vision, else the actual photo pixels (CV), else filename.
    colors = detected.get("color")
    if isinstance(colors, str) and colors:
        color_list = [c.strip() for c in re.split(r"[,\n]", colors) if c.strip()]
    else:
        color_list = photo_cv.get("dominant_colors") or _detect_colors_from_filename(filename)
    material = detected.get("material")
    material_list = [material] if isinstance(material, str) and material else None

    def _clean_attr(val: Any) -> str:
        if not isinstance(val, str):
            return ""
        v = val.strip()
        return "" if v.lower() in ("", "unknown", "n/a", "na", "none", "null") else v

    condition = _clean_attr(detected.get("condition"))
    style = _clean_attr(detected.get("style"))

    allowed = cfg.get_allowed_variants(category, subcategory)
    product_type = cfg.classify_product_type(product_name, category, subcategory)

    # Auto-add size for apparel when the keyword-fallback list didn't already
    # include it (mirrors upload_auto_05 rule).
    is_apparel = any(
        kw in (category + " " + subcategory).lower()
        for kw in ["apparel", "clothing", "fashion", "shirt", "t-shirt", "pants",
                   "dress", "jacket", "lingerie", "bralette", "bra", "underwear"]
    )
    if is_apparel and "size" in cfg.get_allowed_variants(category, subcategory) and "size" not in allowed:
        allowed = allowed + ["size"]

    # Apply the config's ai_rules include/exclude intelligence per product type
    # (liquids → volume not weight, solids → weight not volume, etc.).
    rules_result = _apply_ai_rules(allowed, product_type, cfg)
    allowed = rules_result["allowed"]
    forced_variants = rules_result["forced"]

    allowed = _apply_mutual_exclusion(allowed, cfg)

    # ── Variant suggestion refinement (the "better model") ──────────────
    # The raw config contains ~150 variant axes, many of which are product
    # *metadata* (brand, sku, hs_code, country_of_origin, warranty, …) rather
    # than selectable sellable variants. We strip those out and then rank the
    # remaining real variant axes so the supplier only sees the most relevant
    # ones — capped to keep the matrix usable.
    suggested = _refine_variant_suggestions(
        allowed,
        product_type=product_type,
        color_list=color_list,
        material_list=material_list,
        cfg=cfg,
        force_include=forced_variants,
    )
    suggested_variants = suggested["keys"]
    variant_options = suggested["options"]

    detected_attributes: Dict[str, Any] = {}
    if color_list:
        detected_attributes["color"] = color_list
    if material_list:
        detected_attributes["material"] = material_list
    if brand:
        detected_attributes["brand"] = brand
    if condition:
        detected_attributes["condition"] = condition
    if style:
        detected_attributes["style"] = style
    detected_attributes.setdefault("product_type", product_type)

    # Generative description (from the structured Ollama result, else heuristic).
    if ollama_content:
        generated_description = ollama_content.get("english_description") or _generate_description(
            product_name, category, subcategory, color_list, material_list, brand)
        arabic_title = ollama_content.get("arabic_title", "")
        arabic_description = ollama_content.get("arabic_description", "")
        english_title = ollama_content.get("english_title") or product_name
        bullet_points_en = ollama_content.get("bullet_points_en") or []
        bullet_points_ar = ollama_content.get("bullet_points_ar") or []
    else:
        generated_description = _generate_description(
            product_name, category, subcategory, color_list, material_list, brand)
        arabic_title = ""
        arabic_description = ""
        english_title = product_name
        bullet_points_en = []
        bullet_points_ar = []
    seo_tags = _generate_tags(product_name, category, subcategory, color_list, material_list, brand)

    # ── Photo-driven upgrades from the vision/text model ────────────────
    # When Ollama produced a structured result, prefer its tag + variant
    # suggestions (derived from the actual photo) over the heuristic/config
    # fallbacks. This is what makes the analyzer "read" the image rather than
    # guess from the filename.
    variant_labels_override: Dict[str, str] = {}
    vision_payload = ollama_content if isinstance(ollama_content, dict) else None
    if vision_payload:
        vision_tags = vision_payload.get("suggested_tags")
        if isinstance(vision_tags, list) and vision_tags:
            clean_tags = [str(t).strip().lower() for t in vision_tags if str(t).strip()]
            if clean_tags:
                seo_tags = clean_tags[:15]

        vision_variants = vision_payload.get("suggested_variants")
        if isinstance(vision_variants, list) and vision_variants:
            vkeys: List[str] = []
            vopts: Dict[str, List[str]] = {}
            for item in vision_variants:
                if not isinstance(item, dict):
                    continue
                axis = str(item.get("axis") or "").strip().lower()
                if not axis or axis in _NON_VARIANT_KEYS:
                    continue
                if axis in vkeys:
                    continue
                vkeys.append(axis)
                opts = [str(o).strip() for o in (item.get("options") or []) if str(o).strip()]
                variant_labels_override[axis] = str(item.get("label") or axis).strip().title()
                vopts[axis] = opts[:12] if opts else cfg.extract_variant_options(axis)[:12]
            if vkeys:
                suggested_variants = vkeys
                variant_options = vopts

    return {
        "product_name_hint": product_name,
        "suggested_category": category,
        "suggested_subcategory": subcategory,
        "suggested_brand": brand,
        "detected_attributes": detected_attributes,
        "suggested_variants": suggested_variants or ["color"],
        "variant_options": variant_options,
        "product_description": generated_description,
        "suggested_tags": seo_tags,
        # Extra helpers for the frontend to build a smarter UX.
        "product_type": product_type,
        # Smart auto-pricing (editable default on the pricing panel).
        **suggest_price(product_type, product_name, category),
        "variant_labels": {
            k: variant_labels_override.get(k) or cfg.get_variant_info(k).get("name", k.title())
            for k in suggested_variants
        },
        # Photo-analysis signals (dominant colours, background complexity) —
        # surfaced in the UI so the supplier can see what the AI "saw".
        "photo_analysis": {
            "dominant_colors": photo_cv.get("dominant_colors", []),
            "background": photo_cv.get("background", "unknown"),
            "bg_complexity": photo_cv.get("bg_complexity", 0.0),
            "suggested_bg_preset": photo_cv.get("suggested_bg_preset"),
        },
        # EN/AR marketing copy (powers the AI Interview + auto-fill).
        "english_title": english_title,
        "english_description": generated_description,
        "arabic_title": arabic_title,
        "arabic_description": arabic_description,
        "bullet_points_en": bullet_points_en,
        "bullet_points_ar": bullet_points_ar,
        "source": "ollama" if (vision_prose or ollama_content) else "heuristic",
    }


# Variant axes that are product *metadata* rather than selectable sellable
# variants. Excluded from the suggested-variants matrix to avoid clutter.
_NON_VARIANT_KEYS = {
    "brand", "sku", "upc", "hs_code", "country_of_origin", "importer",
    "manufacturer", "condition", "grade", "quantity_per_pack", "pack_size",
    "author", "publisher", "pages", "isbn", "edition", "signed", "language",
    "binding", "genre", "license_type", "subscription_duration",
    "delivery_method", "service_duration", "service_location",
    "customization_options", "production_time", "handmade", "vintage",
    "rarity", "fragile", "hazardous", "perishable", "temperature_requirements",
    "allergen_info", "expiry_date", "shelf_life", "storage_instructions",
    "ingredients", "nutritional_info", "serving_size", "servings_per_container",
    "certification", "organic", "dietary", "scent_strength", "fragrance_family",
    "notes", "concentration", "platform", "warranty", "assembly_required",
    "power_source", "closure_type", "heel_height", "shoe_width", "season",
    "occasion",
}


def _refine_variant_suggestions(
    allowed: List[str],
    product_type: str,
    color_list: List[str],
    material_list: Optional[List[str]],
    cfg: "VariantConfig",
    force_include: Optional[set] = None,
) -> Dict[str, Any]:
    """
    Turn the raw allowed-variant list into a ranked, capped set of *real*
    sellable variant axes with example option lists.

    Priority order keeps the universal axes (color/size/material/pattern/gender)
    first, then appends the most category-relevant axes (storage/ram/screen_size
    for electronics, volume/scent for beauty, plating/gemstone for jewelry, …).
    A hard cap of 6 keeps the variant matrix manageable for suppliers.
    """
    forced = force_include or set()
    real = [k for k in allowed if k not in _NON_VARIANT_KEYS or k in forced]

    priority = [
        "color", "size", "material", "pattern", "gender",
        "storage", "ram", "model", "screen_size", "connectivity",
        "processor", "operating_system", "battery_life", "water_resistance",
        "plating", "karat", "gemstone", "chain_length", "watch_strap",
        "watch_movement", "ring_size", "bracelet_size",
        "volume", "weight", "scent", "skin_type", "spf", "flavor",
        "capacity", "voltage", "wattage", "energy_rating", "dimensions",
        "color_temperature", "age_group", "toy_type",
        "car_fitment", "vehicle_type", "fuel_type", "transmission", "year",
        "sport_type", "sleeve_length", "neckline", "fit",
    ]
    # ai_rules-mandated axes (e.g. furniture → dimensions) are ranked ahead of
    # generic axes so the config's intent survives the 6-axis cap.
    ranked = sorted(
        real,
        key=lambda k: (
            0 if k in forced else 1,
            priority.index(k) if k in priority else 999,
            k,
        ),
    )
    capped = ranked[:6]

    options: Dict[str, List[str]] = {}
    for key in capped:
        if key == "color" and color_list:
            options[key] = color_list
        elif key == "material" and material_list:
            options[key] = material_list
        else:
            options[key] = cfg.extract_variant_options(key)

    return {"keys": capped, "options": options}


# Singleton config
_CONFIG = VariantConfig()

