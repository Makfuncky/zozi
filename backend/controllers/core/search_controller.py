"""controllers.core.search_controller controller.

Business logic is delegated to services.core.search_service (routers -> controllers -> services)."""

from services.core.search_service import (
    CATEGORY_SYNONYMS, COLOR_ALIASES, FILLER_PAT, NUMERIC_SIZE_VALUE_PAT, PRICE_KEYWORDS, QUALITY_PATTERNS,
    QUERY_STOPWORDS, REQUEST_PAT, SIZE_NORMALIZATION, TEXT_SEARCH_FIELDS, TEXT_SIZE_VALUE_PAT, _ABOVE_PAT,
    _BETWEEN_PAT, _UNDER_PAT, _build_postgres_search_document, _build_postgres_tsquery, _database_supports_postgres_fts, _deserialize_sizes,
    _extract_color, _extract_quality_preferences, _extract_size, _extract_terms, _normalize_query_text, _normalize_size_value,
    _product_search_blob, _resolve_brand_from_catalog, _score_product, _serialize_product, _serialize_recommendation_product, _sort_ranked_products,
    _strip_phrase, get_recommendations, parse_query, smart_search, smart_search_from_parsed
)

__all__ = [
    "CATEGORY_SYNONYMS", "COLOR_ALIASES", "FILLER_PAT", "NUMERIC_SIZE_VALUE_PAT", "PRICE_KEYWORDS", "QUALITY_PATTERNS",
    "QUERY_STOPWORDS", "REQUEST_PAT", "SIZE_NORMALIZATION", "TEXT_SEARCH_FIELDS", "TEXT_SIZE_VALUE_PAT", "_ABOVE_PAT",
    "_BETWEEN_PAT", "_UNDER_PAT", "_build_postgres_search_document", "_build_postgres_tsquery", "_database_supports_postgres_fts", "_deserialize_sizes",
    "_extract_color", "_extract_quality_preferences", "_extract_size", "_extract_terms", "_normalize_query_text", "_normalize_size_value",
    "_product_search_blob", "_resolve_brand_from_catalog", "_score_product", "_serialize_product", "_serialize_recommendation_product", "_sort_ranked_products",
    "_strip_phrase", "get_recommendations", "parse_query", "smart_search", "smart_search_from_parsed"
]
