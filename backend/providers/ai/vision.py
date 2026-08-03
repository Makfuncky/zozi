from __future__ import annotations

"""
Vision Provider
===============
AI-powered vision analysis for product images with Ollama integration.
Test file: backend/tests/_test_provider/test_vision.py
"""
import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .text import _ollama_chat, _ollama_vision_chat, _extract_json, _extract_variant_from_text, _extract_product_name, _extract_tags

logger = logging.getLogger(__name__)


class settings:
    ollama_text_model = "gpt-4o-mini"
    ollama_model = "gpt-4o-mini"
    ollama_base_url = "http://localhost:11434"

# ============================================================================
# REFERENCE
# ============================================================================
# This module provides AI-powered vision analysis for product images.
# It integrates with Ollama for vision-based product detection and
# provides category normalization, variant detection, and price suggestion.
#
# The pipeline supports:
# - analyze_product_image: Vision AI product analysis (from upload_auto_05.py)
# - classify_product_type: Product type detection (from MasterAttributeDatabase)
# - suggest_price: AI price suggestion
# - normalize_category: Keyword-based category normalization
#
# Test file: backend/tests/_test_provider/test_vision.py
# Run: python -m pytest backend/tests/_test_provider/test_vision.py -v


@dataclass
class VariantConfig:
    """Configuration for product variant detection."""

    variant_type: str = "color"
    name: str = ""
    prompt: str = ""
    type: str = "text"
    categories: List[str] = field(default_factory=list)
    product_types: List[str] = field(default_factory=list)
    mutually_exclusive_with: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "variant_type": self.variant_type,
            "name": self.name,
            "prompt": self.prompt,
            "type": self.type,
            "categories": self.categories,
            "product_types": self.product_types,
            "mutually_exclusive_with": self.mutually_exclusive_with,
        }


def classify_product_type(product_name: str, category: str, subcategory: str = "") -> str:
    """Classify product type from name, category, and subcategory.

    Mirrors MasterAttributeDatabase.classify_product_type from upload_auto_05.py.
    Uses keyword matching to determine the product type:
    clothing, electronic, furniture, appliance, jewelry, beauty, etc.

    Args:
        product_name: Product name string.
        category: Product category.
        subcategory: Product subcategory.

    Returns:
        Normalized product type string.
    """
    text = f"{product_name} {category} {subcategory}".lower()

    # Product type keywords (mirrors zozi_variant_config.json categories)
    type_keywords = {
        "clothing": ["shirt", "dress", "pant", "jean", "jacket", "coat", "sweater", "hoodie", "shorts", "skirt", "blouse", "top", "t-shirt", "lingerie", "bra", "underwear", "swimwear", "sock", "sportswear", "activewear"],
        "electronic": ["phone", "laptop", "computer", "tablet", "headphone", "camera", "gadget", "smartphone", "charger", "cable", "battery", "speaker", "monitor", "keyboard", "mouse", "tv", "console", "drone"],
        "furniture": ["sofa", "chair", "table", "bed", "desk", "cabinet", "shelf", "drawer", "wardrobe", "couch", "ottoman", "stool"],
        "appliance": ["refrigerator", "washing", "dryer", "oven", "microwave", "dishwasher", "vacuum", "air conditioner", "heater", "fan", "kettle", "toaster", "blender"],
        "jewelry": ["necklace", "ring", "bracelet", "earring", "pendant", "chain", "watch", "bangle", "cufflink", "brooch"],
        "beauty": ["perfume", "cream", "serum", "lotion", "makeup", "lipstick", "foundation", "eyeshadow", "mascara", "skincare", "shampoo", "soap", "cosmetic"],
        "shoes": ["shoe", "sneaker", "boot", "sandal", "loafer", "heel", "pump", "flip-flop", "trainer", "runner"],
        "accessory": ["bag", "belt", "hat", "cap", "scarf", "glove", "wallet", "sunglass", "watch", "backpack"],
        "food": ["snack", "drink", "grocery", "organic", "coffee", "tea", "chocolate", "food", "beverage"],
        "toy": ["toy", "game", "puzzle", "doll", "action figure", "board game", "lego", "plush"],
        "book": ["book", "novel", "textbook", "magazine", "journal"],
        "automotive": ["car", "auto", "vehicle", "tire", "engine", "accessory", "tool"],
        "sport": ["ball", "racket", "bat", "glove", "helmet", "mat", "dumbbell", "yoga", "fitness", "gym"],
        "decor": ["lamp", "cushion", "rug", "curtain", "vase", "frame", "candle", "wall art", "mirror"],
        "pet": ["pet", "dog", "cat", "bird", "fish", "treat", "toy"],
        "general": [],
    }

    for ptype, keywords in type_keywords.items():
        if any(kw in text for kw in keywords):
            return ptype

    # Fallback: check category name
    cat_lower = f"{category} {subcategory}".lower()
    for ptype in ["clothing", "electronics", "furniture", "jewelry", "beauty"]:
        if ptype in cat_lower:
            return ptype

    return "general"


def suggest_price(
    image_bytes: bytes,
    product_name: str = "",
    category: str = "",
) -> Dict[str, Any]:
    """Suggest a price for a product based on image and metadata.

    Uses Ollama vision chat for AI price estimation. Falls back to
    auto-price based on product type when Ollama is unavailable.

    Args:
        image_bytes: Raw image bytes.
        product_name: Product name.
        category: Product category.

    Returns:
        Dict with suggested_price, confidence, and reasoning.
    """
    prompt = (
        f"Analyze this product image and suggest a retail price. "
        f"Product: {product_name}, Category: {category}. "
        f"Return JSON with suggested_price and confidence."
    )

    response = _ollama_chat(prompt)
    data = _extract_json(response)

    if data and isinstance(data, dict):
        return {
            "suggested_price": data.get("suggested_price", 0),
            "confidence": data.get("confidence", 0.5),
            "reasoning": data.get("reasoning", ""),
        }

    # Fallback: auto-price by type
    DEFAULT_PRICE_BY_TYPE = {
        "electronic": 45.0, "clothing": 19.0, "furniture": 85.0, "appliance": 55.0,
        "jewelry": 29.0, "beauty": 15.0, "food": 8.0, "toy": 22.0,
        "automotive": 40.0, "book": 12.0, "sport": 25.0, "decor": 18.0,
        "pet": 16.0, "shoes": 35.0, "accessory": 20.0, "general": 19.0,
    }
    ptype = classify_product_type(product_name, category)
    return {
        "suggested_price": DEFAULT_PRICE_BY_TYPE.get(ptype, 19.0),
        "confidence": 0.3,
        "reasoning": f"Auto-priced as {ptype}",
    }


def normalize_category(product_name: str, description: str = "") -> str:
    """Normalize a product category from name and description.

    Args:
        product_name: Product name.
        description: Product description.

    Returns:
        Normalized category string.
    """
    text = f"{product_name} {description}".lower()

    category_keywords = {
        "electronics": ["phone", "laptop", "computer", "tablet", "headphone", "camera", "gadget", "tech", "smartphone", "charger", "cable", "battery", "speaker", "monitor", "keyboard", "mouse", "tv", "console"],
        "fashion": ["cloth", "dress", "shirt", "t-shirt", "shoes", "jeans", "jacket", "wear", "outfit", "sneaker", "apparel", "clothing", "hat", "cap", "belt", "scarf", "lingerie", "bra"],
        "home": ["furniture", "decor", "kitchen", "sofa", "bed", "home", "lamp", "cushion", "rug", "curtain", "furniture"],
        "sports": ["sport", "fitness", "gym", "yoga", "exercise", "running", "athletic", "ball", "mat", "dumbbell"],
        "beauty": ["beauty", "cosmetic", "skincare", "makeup", "perfume", "cream", "serum", "lotion", "soap", "shampoo"],
        "food": ["food", "snack", "drink", "grocery", "organic", "coffee", "tea", "chocolate", "beverage"],
        "toys": ["toy", "game", "kids", "children", "play", "doll", "puzzle", "action figure"],
        "books": ["book", "novel", "textbook", "reading", "literature", "magazine"],
        "automotive": ["car", "auto", "vehicle", "tire", "engine", "accessories", "automotive"],
        "jewelry": ["jewelry", "necklace", "ring", "bracelet", "earring", "watch", "pendant", "chain"],
    }

    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in text:
                return category

    return "general"


def analyze_product_image(
    image_bytes: bytes,
    filename: str = "",
    generate_copy: bool = False,
    use_vision: bool = True,
    subcategory: str = "",
) -> Dict[str, Any]:
    """Analyze a product image and extract structured data.

    Enhanced version that mirrors the upload_auto_05.py analysis pipeline:
    1. Uses Ollama vision for initial product detection
    2. Extracts JSON with phi3:mini fallback
    3. Falls back to keyword-based extraction when vision fails
    4. Classifies product type for variant selection

    Args:
        image_bytes: Raw image bytes.
        filename: Original filename (used for extension hints).
        generate_copy: Whether to generate marketing copy.
        use_vision: Whether to use vision model for analysis.
        subcategory: Optional subcategory hint.

    Returns:
        Dict with product analysis results including name, category,
        tags, description, color, variants, and product_type.
    """
    result: Dict[str, Any] = {
        "name": "",
        "category": "",
        "subcategory": subcategory,
        "tags": [],
        "description": "",
        "color": "",
        "materials": [],
        "variants": {},
        "copy": "",
        "product_type": "general",
        "source": "fallback",
    }

    if use_vision and image_bytes:
        vision_prompt = (
            "Analyze this product image carefully. Extract ALL visible information:\n"
            "- product_name: The product name/title\n"
            "- category: The product category (Electronics, Fashion, Home, Beauty, Food, Sports, Toys, Jewelry, Automotive, Books, General)\n"
            "- color: The dominant color(s)\n"
            "- material: The material(s) the product is made of\n"
            "- tags: 3-5 relevant tags\n"
            "- description: A 1-2 sentence product description\n"
            "Return ONLY valid JSON with these fields."
        )
        vision_response = _ollama_vision_chat(vision_prompt, image_bytes)
        vision_data = _extract_json(vision_response)

        if vision_data and isinstance(vision_data, dict):
            result["name"] = vision_data.get("product_name") or vision_data.get("name", "")
            result["category"] = vision_data.get("category", "")
            result["color"] = vision_data.get("color", "")
            result["description"] = vision_data.get("description", "")
            tags = vision_data.get("tags", [])
            result["tags"] = tags if isinstance(tags, list) else [str(tags)]
            material = vision_data.get("material", "")
            if material:
                result["materials"] = [material]
            result["source"] = "vision_ai"

    if not result["name"]:
        result["name"] = _extract_product_name(filename)

    if not result["category"]:
        result["category"] = normalize_category(result["name"], result["description"])

    if not result["tags"]:
        result["tags"] = _extract_tags("", result["category"])

    variant_data = _extract_variant_from_text(result["name"] + " " + result.get("description", ""))
    result["variants"] = variant_data.get("raw_variants", {})

    # Classify product type for variant selection
    result["product_type"] = classify_product_type(
        result["name"], result["category"], subcategory
    )

    if generate_copy:
        materials_str = ", ".join(result["materials"]) if result["materials"] else ""
        color_str = result.get("color", "")
        tags_str = ", ".join(result["tags"])
        copy_prompt = (
            f"Write a short product description for: {result['name']}. "
            f"Category: {result['category']}. "
            f"Color: {color_str}. "
            f"Material: {materials_str}. "
            f"Tags: {tags_str}. "
            f"Return JSON with english_title, english_description, and bullet_points_en."
        )
        copy_response = _ollama_chat(copy_prompt)
        copy_data = _extract_json(copy_response)
        if copy_data and isinstance(copy_data, dict):
            result["copy"] = copy_data.get("english_description", copy_response.strip())
        else:
            result["copy"] = copy_response.strip()

    return result


