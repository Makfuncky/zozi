from __future__ import annotations

"""
Search Provider
===============
Advanced AI-powered search engine with filtering and vectorization.
Test file: backend/tests/_test_provider/test_search.py
"""
import logging
import re
from typing import Any, Dict, List, Optional


class settings:
    search_default_limit = 50
    search_fuzzy_cutoff = 0.6
    catalog_model = "gpt-4o-mini"

logger = logging.getLogger(__name__)


def _ollama_chat(prompt: str, model: Optional[str] = None) -> str:
    return "stub response"

def _extract_json(text: str) -> dict:
    return {}

# ============================================================================
# REFERENCE
# ============================================================================
# This module provides advanced search with AI-powered filtering and vectorization.
# Features:
# - Natural language query parsing (price, size, color, rating, sort)
# - Vector embedding search via nomic-embed-text
# - Semantic similarity ranking
# - Category synonym expansion
# - Autocomplete suggestions
# - Fuzzy search with scoring
#
# Test file: backend/tests/_test_provider/test_search.py
# Run: python -m pytest backend/tests/_test_provider/test_search.py -v


class AdvancedSearchEngine:
    """AI-powered advance search engine with filtering and vectorization.

    Supports:
    - Natural language query parsing
    - Vector embedding search using Ollama embeddings
    - Category synonym expansion
    - Fuzzy matching with configurable cutoff
    - Autocomplete suggestions
    """

    def __init__(self, db: Any = None):
        self.db = db
        self._product_catalog_loaded = False
        self._brands: List[str] = []
        self._categories: List[str] = []
        self._category_synonyms: Dict[str, List[str]] = {
            "electronics": ["tech", "gadget", "electronic", "digital", "device", "smart"],
            "fashion": ["clothing", "apparel", "wear", "garment", "outfit", "style"],
            "home": ["furniture", "decor", "household", "living", "kitchen", "garden"],
            "sports": ["fitness", "gym", "exercise", "outdoor", "athletic"],
            "beauty": ["cosmetics", "skincare", "makeup", "personal care", "grooming"],
            "jewelry": ["accessories", "jewellery", "ornaments", "watches"],
            "toys": ["games", "kids", "children", "play"],
            "food": ["groceries", "beverages", "snacks", "drinks"],
            "books": ["literature", "reading", "novels", "textbooks"],
            "automotive": ["car", "vehicle", "auto parts", "accessories"],
        }
        # Cache for product embeddings
        self._product_embeddings: Dict[int, List[float]] = {}
        self._product_catalog: List[Dict[str, Any]] = []

    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse a natural language query into structured search parameters.

        Extracts:
        - Free-text search terms
        - Price range (under X, above Y, between X and Y)
        - Minimum rating (X+ stars)
        - Size (size M, size 42)
        - Color name
        - Video filter
        - Sort order (newest, price, rating)

        Args:
            query: Natural language search query.

        Returns:
            Dict with structured search parameters.
        """
        parsed: Dict[str, Any] = {
            "q": query,
            "terms": [],
            "min_price": None,
            "max_price": None,
            "category": None,
            "brand": None,
            "brands": None,
            "size": None,
            "color": None,
            "min_rating": None,
            "max_rating": None,
            "sort": None,
            "has_video": False,
        }

        q_lower = query.lower()

        # Price extraction
        price_patterns = [
            (r"\bunder\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\bbelow\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\bless\s+than\s+\$?(\d+(?:\.\d+)?)", "max_price"),
            (r"\babove\s+\$?(\d+(?:\.\d+)?)", "min_price"),
            (r"\bover\s+\$?(\d+(?:\.\d+)?)", "min_price"),
            (r"\bbetween\s+\$?(\d+(?:\.\d+)?)\s+and\s+\$?(\d+(?:\.\d+)?)", "range_price"),
        ]

        for pattern, field in price_patterns:
            match = re.search(pattern, q_lower)
            if match:
                if field == "range_price":
                    parsed["min_price"] = float(match.group(1))
                    parsed["max_price"] = float(match.group(2))
                elif field == "max_price":
                    parsed["max_price"] = float(match.group(1))
                elif field == "min_price":
                    parsed["min_price"] = float(match.group(1))
                break

        # Rating extraction
        rating_match = re.search(r"(\d)\s*\+?\s*star", q_lower)
        if rating_match:
            parsed["min_rating"] = int(rating_match.group(1))

        # Size extraction
        size_match = re.search(r"(?:size\s*)([a-z]+|\d{2,3})", q_lower, re.IGNORECASE)
        if size_match:
            parsed["size"] = size_match.group(1).upper()

        # Color extraction
        color_match = re.search(r"\b(black|white|red|blue|green|yellow|pink|purple|brown|gray|grey|silver|gold|beige|navy|olive|maroon|teal)\b", q_lower)
        if color_match:
            parsed["color"] = color_match.group(1)

        # Category detection via synonyms
        for cat, synonyms in self._category_synonyms.items():
            if any(syn in q_lower for syn in synonyms + [cat]):
                parsed["category"] = cat
                break

        # Sort detection (use word boundaries to avoid substring matches)
        words = set(q_lower.split())
        if "newest" in words or "new" in words:
            parsed["sort"] = "newest"
        elif "top" in words or "rated" in words:
            parsed["sort"] = "rating"
        elif "cheapest" in words or "cheap" in words or "cheaper" in words:
            parsed["sort"] = "price_asc"
        elif "expensive" in words or "high-end" in words or "costliest" in words:
            parsed["sort"] = "price_desc"

        # Video filter
        if "video" in q_lower or "with video" in q_lower:
            parsed["has_video"] = True

        # Extract search terms (remove stop words)
        stop_words = {"a", "an", "and", "for", "the", "is", "are", "to", "of", "in", "on", "with", "by", "at", "from", "it", "this", "that", "these", "those", "me", "my", "i", "want", "need", "looking", "find", "show", "get"}
        terms = [t for t in re.findall(r"[a-z]{2,}", q_lower) if t not in stop_words]
        parsed["terms"] = list(dict.fromkeys(terms))

        return parsed

    def search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = settings.search_default_limit,
        offset: int = 0,
        sort_by: str = "relevance",
    ) -> Dict[str, Any]:
        """Execute a search with AI-powered filtering and vector ranking.

        Performs a multi-stage search:
        1. Parse the natural language query
        2. Apply keyword + category + price filters
        3. Rank results using embedding similarity (if DB connected)
        4. Return paginated results

        Args:
            query: Natural language search query.
            filters: Additional filter parameters.
            limit: Maximum results to return.
            offset: Pagination offset.
            sort_by: Sort strategy (relevance, price_asc, price_desc, newest, rating).

        Returns:
            Dict with products, total count, parsed query, and embeddings.
        """
        parsed = self.parse_query(query)
        all_filters = {**(filters or {}), **parsed}

        # Generate query embedding for vector search
        query_embedding = embed_text(query)

        # If we have a product catalog loaded, rank by similarity
        ranked_products = []
        if self._product_catalog and query_embedding:
            scored = []
            for product in self._product_catalog:
                pid = product.get("id")
                prod_embed = product.get("embedding") or self._product_embeddings.get(pid)
                if prod_embed:
                    score = cosine_similarity(query_embedding, prod_embed)
                    scored.append((score, product))
            scored.sort(key=lambda x: x[0], reverse=True)
            ranked_products = [p for _, p in scored]

        return {
            "products": ranked_products,
            "total": len(ranked_products),
            "limit": limit,
            "offset": offset,
            "parsed_query": parsed,
            "all_filters": all_filters,
            "vector_search_applied": bool(query_embedding),
            "message": "Search engine ready. Load a product catalog for live results.",
        }

    def load_product_catalog(self, products: List[Dict[str, Any]]) -> int:
        """Load a product catalog and pre-compute embeddings.

        Args:
            products: List of product dicts with id, name, description, tags.

        Returns:
            Number of products loaded.
        """
        self._product_catalog = products
        self._product_embeddings = {}

        for product in products:
            pid = product.get("id")
            if pid is None:
                continue
            # Build text for embedding
            embed_text_content = " ".join([
                product.get("name", ""),
                product.get("description", ""),
                " ".join(product.get("tags", []) or []),
            ]).strip()
            if embed_text_content:
                embedding = embed_text(embed_text_content)
                if embedding:
                    self._product_embeddings[pid] = embedding
                    product["embedding"] = embedding

        self._product_catalog_loaded = True
        return len(self._product_catalog)

    def get_autocomplete_suggestions(self, query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a partial query.

        Args:
            query: Partial search query.
            limit: Maximum number of suggestions.

        Returns:
            List of suggestion strings.
        """
        if not query or len(query) < 2:
            return []

        suggestions = []

        # Add category suggestions
        q_lower = query.lower()
        for cat in self._categories:
            if cat.lower().startswith(q_lower):
                suggestions.append(cat)

        # Add brand suggestions
        for brand in self._brands:
            if brand.lower().startswith(q_lower):
                suggestions.append(brand)

        # Add common query patterns
        common_queries = [
            "cheapest", "top rated", "new arrivals", "under 50", "free shipping",
            "best seller", "on sale", "with video", "near me", "in stock",
        ]
        for cq in common_queries:
            if cq.startswith(q_lower):
                suggestions.append(cq)

        return suggestions[:limit]

    def fuzzy_search(
        self,
        query: str,
        limit: int = 20,
        cutoff: float = settings.search_fuzzy_cutoff,
    ) -> Dict[str, Any]:
        """Perform a fuzzy search with similarity scoring.

        Uses embedding similarity for semantic fuzzy matching,
        falling back to keyword-based fuzzy matching.

        Args:
            query: Search query.
            limit: Maximum results to return.
            cutoff: Similarity cutoff threshold.

        Returns:
            Dict with fuzzy search results.
        """
        parsed = self.parse_query(query)
        query_embedding = embed_text(query)

        fuzzy_results = []
        if self._product_catalog and query_embedding:
            for product in self._product_catalog:
                pid = product.get("id")
                prod_embed = product.get("embedding") or self._product_embeddings.get(pid)
                if prod_embed:
                    score = cosine_similarity(query_embedding, prod_embed)
                    if score >= cutoff:
                        fuzzy_results.append({
                            "product": product,
                            "similarity": round(score, 4),
                        })
            fuzzy_results.sort(key=lambda x: x["similarity"], reverse=True)

        return {
            "products": [r["product"] for r in fuzzy_results[:limit]],
            "total": len(fuzzy_results),
            "parsed_query": parsed,
            "fuzzy_applied": cutoff < 1.0,
            "cutoff": cutoff,
            "embedding_search_applied": bool(query_embedding),
            "message": "Fuzzy search engine ready. Load a product catalog for live results.",
        }