from __future__ import annotations

"""
AI Categorization Provider
=========================
AI-powered product category prediction using keyword matching and LLM inference.
Integrates with the existing Ollama text provider for intelligent categorization.

Provides:
- predict_category: Predict category from product title/description/image
- batch_predict: Batch prediction for multiple products
- confidence scoring with fallback to keyword matching

The provider gracefully degrades when AI/LLM is unavailable (Law 30).
"""
import json
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

HAS_CATEGORIZATION = True

__all__ = [
    "HAS_CATEGORIZATION",
    "CategoryPrediction",
    "predict_category",
    "batch_predict",
    "get_category_suggestions",
]


@dataclass
class CategoryPrediction:
    """A single category prediction with confidence score."""

    category_id: int
    category_name: str
    slug: str
    confidence: float  # 0.0 to 1.0
    path: str = ""  # materialized path
    source: str = "keyword"  # "keyword", "llm", "image"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category_id": self.category_id,
            "category_name": self.category_name,
            "slug": self.slug,
            "confidence": self.confidence,
            "path": self.path,
            "source": self.source,
        }


# Keyword-based category mapping for fast, offline prediction
# Maps normalized keywords to (category_id, category_name, slug)
_CATEGORY_KEYWORDS: Dict[str, tuple[int, str, str]] = {
    # Electronics
    "phone": (10101, "Smartphones", "smartphones"),
    "iphone": (10101, "Smartphones", "smartphones"),
    "samsung galaxy": (10101, "Smartphones", "smartphones"),
    "laptop": (10201, "Laptops", "laptops"),
    "macbook": (10201, "Laptops", "laptops"),
    "computer": (10202, "Desktop Computers", "desktop-computers"),
    "tablet": (10203, "Tablets", "tablets"),
    "ipad": (10203, "Tablets", "tablets"),
    "headphone": (10301, "Headphones", "headphones"),
    "earbud": (10302, "Earbuds", "earbuds"),
    "speaker": (10303, "Speakers", "speakers"),
    "camera": (10401, "Digital Cameras", "digital-cameras"),
    "dslr": (10402, "DSLR Cameras", "dslr-cameras"),
    "drone": (10407, "Drones", "drones"),
    "smartwatch": (10501, "Smartwatches", "smartwatches"),
    "fitness tracker": (10502, "Fitness Trackers", "fitness-trackers"),
    "vr headset": (10504, "VR Headsets", "vr-headsets"),
    "console": (10601, "Gaming Consoles", "gaming-consoles"),
    "playstation": (10601, "Gaming Consoles", "gaming-consoles"),
    "xbox": (10601, "Gaming Consoles", "gaming-consoles"),
    "nintendo": (10601, "Gaming Consoles", "gaming-consoles"),
    "video game": (10606, "Video Games", "video-games"),
    # Fashion - Women
    "dress": (20101, "Dresses", "dresses"),
    "gown": (20101, "Dresses", "dresses"),
    "abaya": (20105, "Abayas", "abayas"),
    "hijab": (20106, "Jilbabs & Hijabs", "jilbabs-hijabs"),
    "jilbab": (20106, "Jilbabs & Hijabs", "jilbabs-hijabs"),
    "blouse": (20102, "Tops & Blouses", "tops-blouses"),
    "skirt": (20104, "Skirts", "skirts"),
    "women jacket": (20107, "Outerwear & Jackets", "outerwear-jackets"),
    # Fashion - Men
    "shirt": (20201, "Shirts", "shirts"),
    "t-shirt": (20202, "T-Shirts & Polos", "t-shirts-polos"),
    "polo": (20202, "T-Shirts & Polos", "t-shirts-polos"),
    "suit": (20205, "Suits & Blazers", "suits-blazers"),
    "thobe": (20210, "Thobes & Dishdasha", "thobes-dishdasha"),
    "dishdasha": (20210, "Thobes & Dishdasha", "thobes-dishdasha"),
    # Footwear
    "sneaker": (20403, "Sneakers & Athletic", "sneakers-athletic"),
    "shoe": (204, "Footwear", "footwear"),
    "sandal": (20404, "Sandals & Slippers", "sandals-slippers"),
    "boot": (20405, "Boots", "boots"),
    "heel": (20401, "Women's Shoes", "womens-shoes"),
    # Bags
    "handbag": (20501, "Handbags", "handbags"),
    "backpack": (20502, "Backpacks", "backpacks"),
    "wallet": (20504, "Wallets & Cardholders", "wallets-cardholders"),
    "luggage": (20503, "Travel Luggage", "travel-luggage"),
    "suitcase": (20503, "Travel Luggage", "travel-luggage"),
    # Jewelry
    "necklace": (20601, "Necklaces & Pendants", "necklaces-pendants"),
    "ring": (20602, "Rings", "rings"),
    "bracelet": (20603, "Bracelets & Bangles", "bracelets-bangles"),
    "earring": (20604, "Earrings", "earrings"),
    "watch": (20605, "Watches", "watches"),
    # Beauty
    "perfume": (40401, "Women's Perfume", "womens-perfume"),
    "cologne": (40402, "Men's Cologne", "mens-cologne"),
    "oud": (40404, "Oud & Bakhoor", "oud-bakhoor"),
    "bakhoor": (40404, "Oud & Bakhoor", "oud-bakhoor"),
    "lipstick": (40203, "Lip Makeup", "lip-makeup"),
    "foundation": (40201, "Face Makeup", "face-makeup"),
    "mascara": (40202, "Eye Makeup", "eye-makeup"),
    "shampoo": (40301, "Shampoo & Conditioner", "shampoo-conditioner"),
    "moisturizer": (40102, "Moisturizers", "moisturizers"),
    "serum": (40103, "Serums & Treatments", "serums-treatments"),
    "sunscreen": (40104, "Sunscreen", "sunscreen"),
    # Home
    "sofa": (30101, "Living Room Furniture", "living-room-furniture"),
    "chair": (30101, "Living Room Furniture", "living-room-furniture"),
    "table": (30103, "Dining Room Furniture", "dining-room-furniture"),
    "bed": (30102, "Bedroom Furniture", "bedroom-furniture"),
    "desk": (30104, "Office Furniture", "office-furniture"),
    "pillow": (30405, "Pillows", "pillows"),
    "towel": (30406, "Towels", "towels"),
    "mattress": (30102, "Bedroom Furniture", "bedroom-furniture"),
    # Sports
    "football": (60201, "Football", "football"),
    "basketball": (60202, "Basketball", "basketball"),
    "tennis": (60203, "Tennis", "tennis"),
    "cricket": (60204, "Cricket", "cricket"),
    "yoga": (60103, "Yoga & Pilates", "yoga-pilates"),
    "dumbbell": (60102, "Strength Training", "strength-training"),
    "treadmill": (60101, "Cardio Equipment", "cardio-equipment"),
    # Automotive
    "car": (7, "Automotive", "automotive"),
    "helmet": (70301, "Helmets", "helmets"),
    "engine oil": (70401, "Engine Oil", "engine-oil"),
    # Baby
    "diaper": (80101, "Diapers & Wipes", "diapers-wipes"),
    "stroller": (80201, "Strollers & Prams", "strollers-prams"),
    "baby bottle": (80102, "Baby Feeding", "baby-feeding"),
    "toy": (80301, "Educational Toys", "educational-toys"),
    "doll": (80302, "Action Figures & Dolls", "action-figures-dolls"),
    "lego": (80303, "Building Toys", "building-toys"),
    # Food
    "coffee": (100401, "Coffee", "coffee"),
    "tea": (100402, "Tea", "tea"),
    "chocolate": (100301, "Chocolate & Candy", "chocolate-candy"),
    "snack": (100302, "Chips & Crisps", "chips-crisps"),
    "organic": (100501, "Organic Produce", "organic-produce"),
    # Books
    "book": (90101, "Fiction", "fiction"),
    "novel": (90101, "Fiction", "fiction"),
    "quran": (90105, "Religious & Spiritual", "religious-spiritual"),
    # Digital
    "software": (130101, "Software", "software"),
    "gift card": (130105, "Digital Gift Cards", "digital-gift-cards"),
    "course": (130106, "Online Courses", "online-courses"),
}

# Broader category fallback mapping
_CATEGORY_FALLBACKS: Dict[str, tuple[int, str, str]] = {
    "electronic": (1, "Electronics", "electronics"),
    "fashion": (2, "Fashion", "fashion"),
    "clothing": (2, "Fashion", "fashion"),
    "home": (3, "Home & Garden", "home-garden"),
    "furniture": (3, "Home & Garden", "home-garden"),
    "beauty": (4, "Beauty & Personal Care", "beauty-personal-care"),
    "health": (5, "Health & Wellness", "health-wellness"),
    "sport": (6, "Sports & Outdoors", "sports-outdoors"),
    "car": (7, "Automotive", "automotive"),
    "auto": (7, "Automotive", "automotive"),
    "baby": (8, "Baby & Kids", "baby-kids"),
    "kid": (8, "Baby & Kids", "baby-kids"),
    "book": (9, "Books & Media", "books-media"),
    "food": (10, "Food & Grocery", "food-grocery"),
    "grocery": (10, "Food & Grocery", "food-grocery"),
    "office": (11, "Office & Stationery", "office-stationery"),
    "industrial": (12, "Industrial & Scientific", "industrial-scientific"),
    "service": (13, "Services & Digital", "services-digital"),
    "digital": (13, "Services & Digital", "services-digital"),
    "travel": (14, "Travel & Luggage", "travel-luggage"),
    "luxury": (15, "Luxury & Premium", "luxury-premium"),
    "premium": (15, "Luxury & Premium", "luxury-premium"),
}

# Reverse mapping from slug to (category_id, category_name) for LLM resolution
_SLUG_TO_CATEGORY: Dict[str, tuple[int, str]] = {}
for _mapping in (_CATEGORY_KEYWORDS, _CATEGORY_FALLBACKS):
    for _keyword, (_cat_id, _name, _slug) in _mapping.items():
        _SLUG_TO_CATEGORY[_slug] = (_cat_id, _name)


def _normalize_text(text: str) -> str:
    """Normalize text for keyword matching."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s\-&]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _keyword_predict(text: str) -> List[CategoryPrediction]:
    """Predict categories using keyword matching."""
    normalized = _normalize_text(text)
    if not normalized:
        return []

    predictions: Dict[int, CategoryPrediction] = {}

    # Try exact keyword matches first (higher confidence)
    for keyword, (cat_id, name, slug) in _CATEGORY_KEYWORDS.items():
        if keyword in normalized:
            if cat_id not in predictions:
                predictions[cat_id] = CategoryPrediction(
                    category_id=cat_id,
                    category_name=name,
                    slug=slug,
                    confidence=0.85,
                    source="keyword",
                )
            else:
                # Boost confidence for multiple keyword matches
                predictions[cat_id].confidence = min(0.95, predictions[cat_id].confidence + 0.05)

    # Try fallback category matches
    for keyword, (cat_id, name, slug) in _CATEGORY_FALLBACKS.items():
        if keyword in normalized and cat_id not in predictions:
            predictions[cat_id] = CategoryPrediction(
                category_id=cat_id,
                category_name=name,
                slug=slug,
                confidence=0.6,
                source="keyword",
            )

    # Sort by confidence descending
    return sorted(predictions.values(), key=lambda p: p.confidence, reverse=True)


def _llm_predict(text: str) -> List[CategoryPrediction]:
    """Predict categories using LLM inference (Ollama)."""
    try:
        from .text import _ollama_chat
    except ImportError:
        return []

    try:
        prompt = (
            f'Given the product "{text}", suggest the most appropriate product category. '
            "Respond with JSON format: "
            '[{"category": "exact category name", "confidence": 0.9, "slug": "category-slug"}]. '
            "Limit to top 3 suggestions."
        )
        response = _ollama_chat(prompt)
        if not response:
            return []

        # Try to parse JSON response
        try:
            data = json.loads(response)
            predictions = []
            for item in data:
                slug = item.get("slug", "")
                # Resolve category_id from slug mapping
                cat_id, cat_name = _SLUG_TO_CATEGORY.get(
                    slug, (0, item.get("category", ""))
                )
                pred = CategoryPrediction(
                    category_id=cat_id,
                    category_name=cat_name or item.get("category", ""),
                    slug=slug,
                    confidence=float(item.get("confidence", 0.5)),
                    source="llm",
                )
                predictions.append(pred)
            return predictions
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.debug("LLM response not valid JSON: %s", response[:100])
            return []
    except Exception as exc:
        logger.debug("LLM prediction failed: %s", exc)
        return []


def predict_category(
    title: str,
    description: str | None = None,
    image_bytes: bytes | None = None,
    country_code: str | None = None,
    *,
    max_suggestions: int = 5,
) -> List[CategoryPrediction]:
    """Predict product categories from title, description, and/or image.

    Uses keyword matching first, then LLM inference for ambiguous cases.
    Gracefully degrades when LLM is unavailable (Law 30).

    Args:
        title: Product title.
        description: Product description (optional).
        image_bytes: Product image bytes (optional, future use).
        country_code: Country code for localization (optional).
        max_suggestions: Maximum number of suggestions to return.

    Returns:
        List of CategoryPrediction, sorted by confidence descending.
    """
    # Combine text for analysis
    text = title
    if description:
        text = f"{title} {description}"

    # Keyword matching (always available)
    predictions = _keyword_predict(text)

    # If keyword matching didn't find enough, try LLM
    if len(predictions) < 2:
        llm_predictions = _llm_predict(text)
        # Merge LLM predictions (lower priority than keyword)
        existing_ids = {p.category_id for p in predictions}
        for pred in llm_predictions:
            if pred.category_id not in existing_ids:
                pred.confidence *= 0.8  # Slightly lower confidence for LLM-only
                predictions.append(pred)

    return predictions[:max_suggestions]


def batch_predict(
    products: List[Dict[str, Any]],
    *,
    max_suggestions: int = 3,
) -> List[List[CategoryPrediction]]:
    """Predict categories for multiple products.

    Args:
        products: List of product dicts with 'title', 'description' keys.
        max_suggestions: Max suggestions per product.

    Returns:
        List of prediction lists, one per product.
    """
    results = []
    for product in products:
        predictions = predict_category(
            title=product.get("title", ""),
            description=product.get("description"),
            max_suggestions=max_suggestions,
        )
        results.append(predictions)
    return results


def get_category_suggestions(
    text: str,
    *,
    limit: int = 5,
    min_confidence: float = 0.3,
) -> List[Dict[str, Any]]:
    """Get category suggestions as simple dicts (for API responses).

    Args:
        text: Product title or description.
        limit: Maximum suggestions.
        min_confidence: Minimum confidence threshold.

    Returns:
        List of suggestion dicts with category_id, name, slug, confidence.
    """
    predictions = predict_category(text, max_suggestions=limit)
    return [
        pred.to_dict()
        for pred in predictions
        if pred.confidence >= min_confidence
    ]
