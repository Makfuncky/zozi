"""Catalog search service — wires the AI search engine provider into the catalog domain."""
from __future__ import annotations

import logging

from providers.ai.search import AdvancedSearchEngine

logger = logging.getLogger(__name__)

_search_engine = AdvancedSearchEngine()


def load_search_catalog(products: list[dict]) -> int:
    """Load product catalog into the AI search engine."""
    try:
        return _search_engine.load_product_catalog(products)
    except ConnectionError as exc:
        logger.warning("Search embedding provider unreachable: %s", exc)
        return 0
    except Exception as exc:
        logger.warning("Search catalog load failed: %s", exc)
        return 0


def search_products(query: str, filters: dict = None, limit: int = 20) -> dict:
    """Search products using the AI-powered search engine."""
    try:
        return _search_engine.search(query=query, filters=filters, limit=limit)
    except ConnectionError as exc:
        logger.warning("Search provider unreachable: %s", exc)
        return {"products": [], "total": 0, "error": "Search service unavailable"}
    except Exception as exc:
        logger.warning("Search failed: %s", exc)
        return {"products": [], "total": 0, "error": str(exc)}
