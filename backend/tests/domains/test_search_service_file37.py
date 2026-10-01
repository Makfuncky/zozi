"""FILE-37 unit tests: the deprecated catalog search shim must actually forward.

Finding 1 (Architectural): ``backend/domains/catalog/services/search_service.py`` is a
deprecated wrapper around ``domains.catalog.services.search.search_service``, but its
``__all__`` advertised canonical names that were never imported. Every one of those
names was absent from the module namespace, so ``from ... import *`` and
``from ... import parse_query`` both raised ``AttributeError``.

Finding 2 (Test File): the shim had no behavioural test of its own. The only test that
touched it asserted on source text, which is exactly why the missing bindings shipped
undetected -- a string assertion cannot see the module namespace.

These tests are behavioural: they assert what the module namespace actually exposes and
what the legacy helpers actually do.
"""
from __future__ import annotations

import importlib
import inspect
from unittest.mock import MagicMock, patch

import pytest


SHIM = "domains.catalog.services.search_service"
CANONICAL = "domains.catalog.services.search.search_service"

# Names advertised by the shim's __all__ that must be forwarded from the canonical module.
CANONICAL_EXPORTS = (
    "parse_query",
    "smart_search",
    "smart_search_from_parsed",
    "get_recommendations",
    "AdvancedFilterService",
)


@pytest.fixture(scope="module")
def shim():
    return importlib.import_module(SHIM)


@pytest.fixture(scope="module")
def canonical():
    return importlib.import_module(CANONICAL)


class TestRegressionAllResolves:
    """Regression test for the corrected behaviour: every advertised name is bound."""

    def test_all_has_no_unbound_names(self, shim):
        missing = [name for name in shim.__all__ if not hasattr(shim, name)]
        assert missing == [], f"__all__ advertises names absent from the module: {missing}"

    def test_star_import_succeeds(self, shim):
        # The exact failure mode that shipped: `from ... import *` raised AttributeError
        # because five of the names in __all__ were never bound.
        namespace: dict = {}
        exec(f"from {SHIM} import *", namespace)
        for name in shim.__all__:
            assert name in namespace, f"{name} missing after star import"

    @pytest.mark.parametrize("name", CANONICAL_EXPORTS)
    def test_canonical_name_is_canonical_object(self, shim, canonical, name):
        # The shim must forward, not re-implement: identity proves the canonical object
        # is the one being served.
        assert getattr(shim, name) is getattr(canonical, name), (
            f"{name} must be re-exported from {CANONICAL}, not re-implemented here"
        )

    def test_legacy_helpers_keep_their_original_signatures(self, shim, canonical):
        # Frozen behaviour: the legacy helpers stay bound to the provider engine. The
        # canonical API is incompatible and must not be substituted underneath callers.
        assert shim.search_products is not canonical.search_products
        assert list(inspect.signature(shim.search_products).parameters) == [
            "query",
            "filters",
            "limit",
        ]
        assert list(inspect.signature(shim.load_search_catalog).parameters) == ["products"]


class TestErrorPath:
    """Error paths: failures stay explicit and are never hidden by the shim."""

    def test_unknown_name_raises_import_error(self, shim):
        # No try/except is wrapped around the canonical import, so a genuinely broken
        # canonical module fails loudly instead of degrading into a fake facade.
        assert "no_such_search_symbol" not in shim.__all__
        with pytest.raises(ImportError):
            exec(f"from {SHIM} import no_such_search_symbol", {})

    def test_legacy_search_products_reports_provider_unreachable(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.search.side_effect = ConnectionError("timeout")
            result = shim.search_products("shoes", limit=10)
        engine.search.assert_called_once_with(query="shoes", filters=None, limit=10)
        assert result == {"products": [], "total": 0, "error": "Search service unavailable"}

    def test_legacy_search_products_reports_generic_failure(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.search.side_effect = RuntimeError("boom")
            result = shim.search_products("shoes", filters={"category": "fashion"})
        engine.search.assert_called_once_with(
            query="shoes", filters={"category": "fashion"}, limit=20
        )
        assert result == {"products": [], "total": 0, "error": "boom"}

    def test_legacy_load_search_catalog_reports_failure(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.load_product_catalog.side_effect = ConnectionError("provider down")
            result = shim.load_search_catalog([{"id": 1}])
        engine.load_product_catalog.assert_called_once_with([{"id": 1}])
        assert result == 0

    def test_legacy_load_search_catalog_delegates(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.load_product_catalog.return_value = 42
            assert shim.load_search_catalog([{"id": 1}]) == 42


class TestParseQueryForwarded:
    """parse_query is re-exported from the canonical module and must be callable."""

    def test_parse_query_identity(self, shim, canonical):
        assert shim.parse_query is canonical.parse_query

    def test_parse_query_extracts_price_range(self, shim):
        result = shim.parse_query("show me products under 50")
        assert result["max_price"] == 50
        assert result["min_price"] is None

    def test_parse_query_extracts_category(self, shim):
        result = shim.parse_query("find me a phone")
        assert result["category"] == "electronics"

    def test_parse_query_extracts_sort(self, shim):
        result = shim.parse_query("best rated laptops")
        assert result["sort"] == "rating"


class TestSmartSearchFromParsedForwarded:
    """smart_search_from_parsed is re-exported and must work through the shim."""

    def test_identity(self, shim, canonical):
        assert shim.smart_search_from_parsed is canonical.smart_search_from_parsed

    def test_returns_products_and_parsed(self, shim):
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("domains.catalog.services.search.search_service.cache_or_compute", return_value=[]):
            result = shim.smart_search_from_parsed(
                parsed={"q": "shoes", "terms": [], "min_price": None, "max_price": None, "category": None, "brand": None, "size": None, "color": None, "min_rating": None, "quality": None, "sort": None, "has_video": None},
                limit=5,
                db=mock_db,
                response=mock_response,
            )
        assert "products" in result
        assert "parsed" in result


class TestSmartSearchForwarded:
    """smart_search is re-exported and must work through the shim."""

    def test_identity(self, shim, canonical):
        assert shim.smart_search is canonical.smart_search

    def test_returns_products_and_parsed(self, shim):
        mock_db = MagicMock()
        mock_response = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        with patch("domains.catalog.services.search.search_service.cache_search_results", return_value=None), \
             patch("domains.catalog.services.search.search_service.set_search_results"), \
             patch("domains.catalog.services.search.search_service.cache_or_compute", return_value=[]):
            result = shim.smart_search("shoes", limit=5, db=mock_db, response=mock_response)
        assert "products" in result
        assert "parsed" in result


class TestGetRecommendationsForwarded:
    """get_recommendations is re-exported and must work through the shim."""

    def test_identity(self, shim, canonical):
        assert shim.get_recommendations is canonical.get_recommendations

    def test_returns_recommendations_without_user(self, shim):
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = []
        result = shim.get_recommendations(None, db=mock_db, limit=5)
        assert "products" in result
        assert "results" in result


class TestAdvancedFilterServiceForwarded:
    """AdvancedFilterService is re-exported and must be instantiable through the shim."""

    def test_identity(self, shim, canonical):
        assert shim.AdvancedFilterService is canonical.AdvancedFilterService

    def test_instantiate_and_get_available_filters(self, shim):
        mock_db = MagicMock()
        price_stats_result = MagicMock()
        price_stats_result.min_price = 10
        price_stats_result.max_price = 100
        price_stats_result.avg_price = 50
        mock_db.query.return_value.filter.return_value.with_entities.return_value.first.return_value = price_stats_result
        mock_db.query.return_value.filter.return_value.all.return_value = []
        service = shim.AdvancedFilterService(mock_db)
        with patch("domains.catalog.services.search.search_service.cache_or_compute", return_value={}):
            result = service.get_available_filters()
        assert "price_range" in result
        assert "brands" in result


class TestAdvancedSearchEngineInteraction:
    """The shim must expose the provider's AdvancedSearchEngine and delegate to it."""

    def test_search_engine_is_provider_class(self, shim):
        from providers.ai.search import AdvancedSearchEngine as ProviderEngine
        assert shim.AdvancedSearchEngine is ProviderEngine

    def test_search_engine_instance_created(self, shim):
        assert isinstance(shim._search_engine, shim.AdvancedSearchEngine)

    def test_search_products_delegates_to_provider_engine(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.search.return_value = {"products": [], "total": 0}
            result = shim.search_products("red dress", filters={"color": "red"}, limit=3)
        engine.search.assert_called_once_with(query="red dress", filters={"color": "red"}, limit=3)
        assert result == {"products": [], "total": 0}

    def test_load_search_catalog_delegates_to_provider_engine(self, shim):
        with patch.object(shim, "_search_engine") as engine:
            engine.load_product_catalog.return_value = 7
            result = shim.load_search_catalog([{"id": 1}, {"id": 2}])
        engine.load_product_catalog.assert_called_once_with([{"id": 1}, {"id": 2}])
        assert result == 7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])