"""Unit tests for FILE-55 search_service.py resolutions."""
from __future__ import annotations

import ast
from decimal import Decimal
import os

import pytest


SOURCE_PATH = "domains/catalog/services/search/search_service.py"
MODEL_PATH = "domains/catalog/models/products.py"
EVIDENCE_DIR = "../_audit/resolver/evidence/FILE-55"


def _source() -> str:
    with open(SOURCE_PATH, "r", encoding="utf-8") as f:
        return f.read()


class TestPerf04SqlSideRanking:
    """PERF-04: in-memory _score_product loop removed, SQL-side ts_rank_cd used."""

    def test_score_product_removed(self):
        assert "def _score_product(" not in _source(), "_score_product should be removed"

    def test_sort_ranked_products_removed(self):
        assert "def _sort_ranked_products(" not in _source(), "_sort_ranked_products should be removed"

    def test_build_postgres_search_document_uses_search_vector(self):
        assert "Product.search_vector" in _source(), "Should reference Product.search_vector for SQL-side ranking"

    def test_search_vector_column_exists_in_model(self):
        with open(MODEL_PATH, "r", encoding="utf-8") as f:
            model_src = f.read()
        assert "search_vector" in model_src, "Product model should have search_vector column"


class TestPerf05SingleCountQuery:
    """PERF-05: 4 separate count() replaced with single conditional aggregation."""

    def test_get_active_filters_summary_single_query(self):
        src = _source()
        # Find get_active_filters_summary body
        start = src.index("def get_active_filters_summary")
        end = src.index("def get_filtered_products")
        body = src[start:end]
        # Should not have separate filtered count() calls chained on base_query
        assert 'base_query.filter(Product.video_count > 0).count()' not in body
        assert 'base_query.filter(Product.compare_price.isnot(None), Product.compare_price > Product.price).count()' not in body
        assert 'base_query.filter(Product.stock > 0).count()' not in body

    def test_get_active_filters_summary_uses_case(self):
        assert "case([" in _source(), "Should use case/when for conditional aggregation"


class TestPerf13CursorPagination:
    """PERF-13: cursor-based pagination added to smart_search_from_parsed."""

    def test_smart_search_from_parsed_accepts_cursor(self):
        assert "cursor: Optional[int] = None" in _source(), "smart_search_from_parsed should accept cursor parameter"

    def test_smart_search_from_parsed_uses_cursor_filter(self):
        assert "Product.id < cursor" in _source(), "Should filter by Product.id < cursor for cursor pagination"


class TestPerf10BrandCache:
    """PERF-10: SELECT DISTINCT brand cached with shared key."""

    def test_brand_cache_uses_shared_key(self):
        assert '"search:brand_catalog:all"' in _source(), "Should use shared cache key for brand catalog"

    def test_brand_cache_no_per_query_digest(self):
        assert "q_digest" not in _source(), "Should not use per-query digest for brand cache key"


class TestAp08DecimalMonetary:
    """AP-08: float() monetary conversions replaced with Decimal."""

    def test_decimal_imported(self):
        assert "from decimal import Decimal" in _source(), "Decimal should be imported"

    def test_price_stats_uses_decimal(self):
        assert "Decimal(result.min_price)" in _source() or "Decimal(result.avg_price)" in _source(), \
            "Price stats should use Decimal"

    def test_filter_prices_use_decimal(self):
        src = _source()
        assert 'Decimal(str(filters["min_price"]))' in src or 'Decimal(str(all_filters["min_price"]))' in src, \
            "Filter price comparisons should use Decimal"

    def test_serialize_product_uses_decimal_for_price(self):
        assert "Decimal(product.price)" in _source(), "Product serialization should use Decimal for price"

    def test_search_products_uses_decimal_for_price(self):
        assert "Decimal(p.price)" in _source(), "search_products should use Decimal for price"

    def test_visual_search_uses_decimal_for_price(self):
        assert 'Decimal(row["price"])' in _source(), "fetch_visually_similar_products should use Decimal for price"

    def test_parse_query_uses_decimal_for_prices(self):
        assert "Decimal(m_between.group(1))" in _source(), "parse_query should use Decimal for price parsing"

    def test_price_keywords_use_decimal(self):
        assert 'Decimal("50.0")' in _source(), "PRICE_KEYWORDS should use Decimal values"


class TestAp11SizeNormalization:
    """AP-11: hardcoded 'xxxl': 'XXXL' removed, fallback handles it."""

    def test_xxxl_mapping_removed(self):
        assert '"xxxl": "XXXL"' not in _source(), "Hardcoded xxxl mapping should be removed"

    def test_normalize_size_uses_fallback(self):
        assert "raw_size.strip().upper()" in _source(), "Should use fallback upper() normalization"


class TestEvidenceFiles:
    """Verify evidence outputs."""

    def test_evidence_dir_exists(self):
        assert os.path.isdir(EVIDENCE_DIR), "Evidence directory should exist"


class TestNoNewFloatMonetary:
    """Ensure no new monetary float() calls remain."""

    def test_no_monetary_float_in_serialization(self):
        src = _source()
        # Extract _serialize_product definitions and check they don't use float() for price
        lines = src.split("\n")
        for i, line in enumerate(lines):
            if "def _serialize_product" in line:
                # Check next ~10 lines for float(price)
                for j in range(i, min(i + 15, len(lines))):
                    if "float(" in lines[j] and "price" in lines[j]:
                        pytest.fail(f"Monetary float() found in _serialize_product at line {j+1}: {lines[j].strip()}")

    def test_no_monetary_float_in_price_stats(self):
        src = _source()
        assert "float(result.min_price)" not in src, "Price stats should not use float()"
        assert "float(result.max_price)" not in src, "Price stats should not use float()"
        assert "float(result.avg_price)" not in src, "Price stats should not use float()"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
