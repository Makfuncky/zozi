import re
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import or_
from sqlalchemy.orm import Session

from data.models import Product


class AISearchService:
    def __init__(self, db: Session):
        self.db = db
        self._load_product_catalog()

    def _load_product_catalog(self) -> None:
        brands = (
            self.db.query(Product.brand)
            .filter(Product.brand.isnot(None), Product.brand != "")
            .distinct()
            .limit(100)
            .all()
        )
        self.brands: Set[str] = {b[0].lower() for b in brands if b[0]}

        categories = (
            self.db.query(Product.category)
            .filter(Product.category.isnot(None), Product.category != "")
            .distinct()
            .limit(50)
            .all()
        )
        self.categories: Set[str] = {c[0].lower() for c in categories if c[0]}

        self.category_synonyms = {
            "electronics": ["phone", "laptop", "computer", "tablet", "headphone", "camera", "gadget", "tech", "smartphone"],
            "fashion": ["cloth", "dress", "shirt", "t-shirt", "shoes", "jeans", "jacket", "wear", "outfit", "sneaker"],
            "home": ["furniture", "decor", "kitchen", "sofa", "bed", "home"],
            "sports": ["sport", "fitness", "gym", "yoga", "exercise", "running", "athletic"],
            "beauty": ["beauty", "cosmetic", "skincare", "makeup", "perfume"],
            "food": ["food", "snack", "drink", "grocery", "organic"],
        }

        self.color_aliases = {
            "black": "black", "white": "white", "blue": "blue", "red": "red",
            "green": "green", "yellow": "yellow", "pink": "pink", "purple": "purple",
            "brown": "brown", "gray": "gray", "grey": "gray", "silver": "silver",
            "gold": "gold", "beige": "beige", "orange": "orange",
        }

    def extract_intent(self, query: str) -> Dict[str, Any]:
        q_lower = query.lower()

        intent = {
            "primary_intent": "product_search",
            "entities": {
                "brands": [],
                "categories": [],
                "attributes": {},
                "price_range": None,
                "rating": None,
            },
            "modifiers": [],
        }

        for brand in self.brands:
            if brand in q_lower:
                intent["entities"]["brands"].append(brand.title())

        for category, synonyms in self.category_synonyms.items():
            if any(syn in q_lower for syn in synonyms):
                intent["entities"]["categories"].append(category)
                break

        price_match = re.search(r"\$(\d+(?:\.\d+)?)", q_lower)
        if price_match:
            intent["entities"]["price_range"] = float(price_match.group(1))

        rating_match = re.search(r"(\d)\s*(\+?\s*)?(star|rating)", q_lower)
        if rating_match:
            intent["entities"]["rating"] = int(rating_match.group(1))

        size_match = re.search(r"(?:size\s*)([a-z]+|\d{2,3})", q_lower, re.IGNORECASE)
        if size_match:
            intent["entities"]["attributes"]["size"] = size_match.group(1).upper()

        for color, normalized in self.color_aliases.items():
            if re.search(rf"\b{color}\b", q_lower):
                intent["entities"]["attributes"]["color"] = normalized
                break

        if "compare" in q_lower or "vs" in q_lower:
            intent["primary_intent"] = "compare_products"
        elif "best" in q_lower or "top" in q_lower:
            intent["primary_intent"] = "recommendation"
        elif "review" in q_lower:
            intent["primary_intent"] = "reviews"

        return intent

    def generate_search_query(self, intent: Dict[str, Any]) -> str:
        query_parts: List[str] = []

        if intent["entities"]["categories"]:
            query_parts.extend(intent["entities"]["categories"])

        if intent["entities"]["brands"]:
            query_parts.extend(intent["entities"]["brands"])

        query_parts.extend(intent["modifiers"])

        return " ".join(query_parts) if query_parts else ""

    def search_with_intent(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
        category_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        intent = self.extract_intent(query)
        optimized_query = self.generate_search_query(intent)

        db_query = self.db.query(Product).filter(
            Product.is_deleted == False,
            Product.is_active == True,
            Product.is_approved == True,
            Product.stock > 0,
        )

        if category_id is not None:
            db_query = db_query.filter(Product.category_id == category_id)

        if intent["entities"]["brands"]:
            db_query = db_query.filter(Product.brand.in_(intent["entities"]["brands"]))

        if intent["entities"]["rating"]:
            db_query = db_query.filter(Product.rating >= intent["entities"]["rating"])

        if optimized_query:
            like_pattern = f"%{optimized_query}%"
            db_query = db_query.filter(
                or_(
                    Product.name.ilike(like_pattern),
                    Product.description.ilike(like_pattern),
                    Product.category.ilike(like_pattern),
                    Product.brand.ilike(like_pattern),
                )
            )

        total = db_query.count()
        products = db_query.offset(offset).limit(limit).all()

        return {
            "products": [self._serialize_product(p) for p in products],
            "total": total,
            "intent": intent,
            "optimized_query": optimized_query,
        }

    def _serialize_product(self, product: Product) -> Dict[str, Any]:
        return {
            "id": product.id,
            "name": product.name,
            "price": float(product.price) if product.price else 0,
            "rating": float(product.rating) if product.rating else 0,
            "brand": product.brand,
            "category": product.category,
            "image_url": product.image_url,
            "stock": product.stock,
        }

    def get_trending_searches(self, limit: int = 10) -> List[str]:
        trending = [
            "laptop",
            "wireless headphones",
            "running shoes",
            "smartphone",
            "yoga mat",
            "coffee maker",
            "bluetooth speaker",
            "winter jacket",
            "fitness tracker",
            "camera lens",
        ]
        return trending[:limit]

    def get_spelling_suggestion(self, query: str) -> Optional[str]:
        if len(query) < 3:
            return None

        similar_products = (
            self.db.query(Product)
            .filter(Product.name.ilike(f"%{query}%"))
            .limit(5)
            .all()
        )

        if similar_products:
            return similar_products[0].name

        return None
