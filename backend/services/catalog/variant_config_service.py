"""
Variant Config Service
======================
Loads `zozi_variant_config.json` at startup and exposes:
  - get_axes_for_category(category, subcategory) — returns applicable variant axes
  - get_material_options(product_type) — chips for fabric/material picker
  - normalize_category(picker_category) — maps UI picker names to config slugs

Used by:
  - GET /supplier/upload/variant-axes  (dynamic frontend endpoint)
  - AI analysis pipeline for axis detection
"""
import json, os, re
from typing import Any

_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..",
    "Working_API", "zozi_ai_upload_session", "zozi_variant_config.json",
)
# Also check a fallback path relative to the backend root
_FALLBACK_PATHS = [
    os.path.join(os.path.dirname(__file__), "..", "data", "zozi_variant_config.json"),
    os.path.join(os.path.dirname(__file__), "..", "zozi_variant_config.json"),
]

# Picker display name → config slug mapping (matches frontend's PICKER_CATEGORY_TO_SLUG)
PICKER_TO_SLUG: dict[str, str] = {
    "Electronics": "electronics",
    "Clothing": "clothing",
    "Home & Garden": "home",
    "Sports & Outdoors": "sports",
    "Books": "books",
    "Beauty & Personal Care": "beauty",
    "Toys & Games": "toys",
    "Automotive": "automotive",
    "Health & Household": "health",
    "Industrial & Scientific": "industrial",
    "Other": "other",
    # Also accept comma-separated canonical list from NLP
    "Home & Kitchen": "home",
    "Pet Supplies": "pet",
    "Office": "office",
}

# Extra slugs that broaden a picker category's coverage
PICKER_EXTRA_SLUGS: dict[str, list[str]] = {
    "Clothing": ["apparel", "fashion"],
    "Home & Garden": ["furniture", "kitchen", "appliances", "garden"],
    "Sports & Outdoors": ["outdoor"],
    "Beauty & Personal Care": ["cosmetics", "skincare", "fragrances"],
    "Automotive": ["automotive_parts"],
    "Electronics": ["phones", "computers", "gaming"],
}


def _load_config() -> dict[str, Any]:
    """Load variant config JSON, trying multiple paths."""
    paths = [_CONFIG_PATH] + _FALLBACK_PATHS
    for p in paths:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    # Fallback: minimal built-in config
    return {
        "version": "1.0.0",
        "description": "Built-in fallback variant config",
        "variants": {},
    }


# Module-level cache (loaded once at import time)
_CONFIG: dict[str, Any] = _load_config()
_VARIANTS: dict[str, Any] = _CONFIG.get("variants", {})


def get_axes_for_category(
    picker_category: str,
    subcategory: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return the variant axes applicable to a given product category.

    Returns a list of axis dicts:
      [{ "key": "color",   "label": "Color",   "options": [...],  "type": "text" },
       { "key": "size",    "label": "Size",    "options": [...],  "type": "text" },
       ...]

    The first axis is typically the primary grouping axis (color for apparel,
    storage for electronics). Options are generated from a cross-category match.
    """
    slug = normalize_category(picker_category)
    extra = PICKER_EXTRA_SLUGS.get(picker_category, [])
    slugs = list(dict.fromkeys([slug] + extra))

    axes: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for s in slugs:
        for key, variant_def in _VARIANTS.items():
            if key in seen_keys:
                continue
            cats = variant_def.get("categories", [])
            if s in cats:
                seen_keys.add(key)
                default_opts = _get_default_options(key, variant_def)
                axes.append({
                    "key": key,
                    "label": variant_def.get("name", key),
                    "label_ar": variant_def.get("name_ar", ""),
                    "type": variant_def.get("type", "text"),
                    "options": default_opts,
                    "mutually_exclusive_with": variant_def.get("mutually_exclusive_with", []),
                })

    return axes


def get_material_options(product_type: str | None = None) -> list[str]:
    """Return material/fabric options, filtered by product type if provided."""
    mat_def = _VARIANTS.get("material", {})
    opts = mat_def.get("default_options", [])
    if not opts:
        # Fallback from prompt text — extract comma-sep list
        prompt = mat_def.get("prompt", "")
        m = re.search(r"comma-sep, e\.g\., (.+)", prompt)
        if m:
            opts = [o.strip() for o in m.group(1).split(",")]
    return opts or [
        "Cotton", "Polyester", "Leather", "Silk", "Wool",
        "Denim", "Linen", "Nylon", "Spandex",
    ]


def get_all_categories() -> list[dict[str, Any]]:
    """Return all known category slugs and their display names."""
    seen: set[str] = set()
    result: list[dict[str, Any]] = []
    for slug, display in PICKER_TO_SLUG.items():
        if display not in seen:
            seen.add(display)
            result.append({"slug": display, "label": slug})
    return result


def normalize_category(picker_category: str) -> str:
    """Convert a UI picker name (e.g. 'Beauty & Personal Care') to a config slug."""
    if not picker_category:
        return "other"
    direct = PICKER_TO_SLUG.get(picker_category)
    if direct:
        return direct
    # Try slugified version
    slug = picker_category.lower().replace("&", "and").replace(" ", "_")
    slug = re.sub(r"[^a-z0-9_]", "", slug)
    if slug in _VARIANTS or slug in [v.get("key") for v in _VARIANTS.values()]:
        return slug
    # Try matching any variant category list
    for key, vdef in _VARIANTS.items():
        cats = vdef.get("categories", [])
        if picker_category.lower() in cats or slug in cats:
            return slug
    return "other"


def _get_default_options(key: str, variant_def: dict[str, Any]) -> list[str]:
    """Return default options for a variant axis, preferring the config's defaults."""
    # Check if there's a default_options field
    if "default_options" in variant_def:
        return variant_def.get("default_options", [])
    # Fallback: parse from prompt text
    prompt = variant_def.get("prompt", "")
    m = re.search(r"comma-sep, e\.g\., (.+)", prompt)
    if m:
        return [o.strip() for o in m.group(1).split(",")]
    return []
