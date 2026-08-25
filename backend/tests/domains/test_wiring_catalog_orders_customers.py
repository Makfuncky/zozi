"""Provider-domain wiring tests for catalog, orders, and customers domains.

Verifies that domain services correctly call their upstream providers
and degrade gracefully when providers are unavailable.
"""

import sys
import types
from unittest.mock import MagicMock, patch


# ── Pre-populate broken legacy imports so the modules under test can load ──
# These imports exist in the source files but their target modules are missing
# or broken in the current legacy codebase. We stub them with MagicMock modules
# so the import succeeds and we can focus on testing provider wiring.

class _MockModule(types.ModuleType):
    """Module subclass that returns a MagicMock for any attribute access.

    Used to stub broken legacy modules so that imports like
    ``from providers.media.ports import AIGenerationLog`` succeed
    without executing the real (missing/broken) module.
    """

    def __getattr__(self, attr: str):
        return MagicMock(name=f"{self.__name__}.{attr}")


def _ensure_mock_module(name: str) -> _MockModule:
    """Install a _MockModule into sys.modules under ``name``."""
    mod = _MockModule(name)
    sys.modules[name] = mod
    return mod


# Stub out the broken import chains that cascade from legacy code.
# Only mock modules that are genuinely missing or have broken internal imports.
# We deliberately avoid mocking ``infrastructure.database`` and its submodules
# because other domain modules (e.g. search_service) need the real SQLAlchemy
# ``Base`` and ORM model classes to function.
for _broken_module in (
    "providers.media.ports",
    "providers.media.services",
    "providers.media.services.ai",
    "infrastructure.database.mixins",
    "domains.comms.models",
    "domains.comms.models.communication",
    "domains.governance.services.infrastructure_audit",
    "infrastructure.utils.audit",
    "infrastructure.utils.constants",
    "domains.orders.utils",
    "domains.orders.utils.order_tracking",
    "domains.governance.services",
    "domains.governance.ports",
    "domains.finance.ports",
    "domains.finance.services",
    "domains.finance.services.ledger",
    "domains.finance.services.ledger.finance_transfer_service",
    "infrastructure.utils.variant_key",
    "infrastructure.utils.auth",
    "infrastructure.utils.cache",
    "providers.payments.stripe",
    "providers.payments.registry",
):
    _ensure_mock_module(_broken_module)


class TestCatalogPreprocessForAI:
    """Tests for _preprocess_for_ai provider wiring."""

    def test_preprocess_for_ai_calls_free_image_tools(self):
        """Verify _preprocess_for_ai calls auto_rotate, auto_lighting, smart_crop, magic_erase."""
        from domains.catalog.services.ai_upload_service import _preprocess_for_ai

        with patch("domains.catalog.services.ai_upload_service.auto_rotate") as mock_rotate, \
             patch("domains.catalog.services.ai_upload_service.auto_lighting") as mock_light, \
             patch("domains.catalog.services.ai_upload_service.smart_crop") as mock_crop, \
             patch("domains.catalog.services.ai_upload_service.magic_erase") as mock_erase:
            mock_rotate.return_value = b"rotated"
            mock_light.return_value = b"lit"
            mock_crop.return_value = b"cropped"
            mock_erase.return_value = b"erased"
            result = _preprocess_for_ai(b"input")
            mock_rotate.assert_called_once_with(b"input")
            mock_light.assert_called_once_with(b"rotated")
            mock_crop.assert_called_once()
            mock_erase.assert_called_once()
            assert result == b"erased"

    def test_preprocess_skips_when_no_cv2(self):
        """When HAS_CV2 is False, return original bytes without calling any tools."""
        from domains.catalog.services.ai_upload_service import _preprocess_for_ai

        with patch("domains.catalog.services.ai_upload_service.HAS_CV2", False), \
             patch("domains.catalog.services.ai_upload_service.auto_rotate") as mock_rotate:
            result = _preprocess_for_ai(b"input")
            mock_rotate.assert_not_called()
            assert result == b"input"


class TestOrdersShippingOptions:
    """Tests for get_order_shipping_options provider wiring."""

    def test_get_order_shipping_options_calls_shipping_provider(self):
        """Verify orders service calls compare_shipping_options with correct args."""
        from domains.orders.services.orders_service import get_order_shipping_options

        with patch("domains.orders.services.orders_service.compare_shipping_options") as mock_compare:
            mock_compare.return_value = [{"carrier": "FedEx", "cost": 10.0}]
            order = MagicMock()
            order.warehouse_country = "US"
            order.warehouse_city = "NYC"
            order.total_weight_kg = 1.0
            order.id = 42
            destination = {"country": "US", "city": "LA"}
            result = get_order_shipping_options(order, destination)
            mock_compare.assert_called_once()
            call_args = mock_compare.call_args
            assert call_args[0][0] == {"country": "US", "city": "NYC"}
            assert call_args[0][1] == destination
            assert call_args[0][2]["weight_kg"] == 1.0
            assert len(result) == 1

    def test_get_order_shipping_options_handles_connection_error(self):
        """When shipping provider is unreachable, return empty list."""
        from domains.orders.services.orders_service import get_order_shipping_options

        with patch("domains.orders.services.orders_service.compare_shipping_options") as mock_compare:
            mock_compare.side_effect = ConnectionError("timeout")
            order = MagicMock()
            order.warehouse_country = "US"
            order.warehouse_city = "NYC"
            order.total_weight_kg = 1.0
            order.id = 42
            result = get_order_shipping_options(order, {"country": "US", "city": "LA"})
            assert result == []

    def test_get_order_shipping_options_handles_generic_exception(self):
        """When shipping calculation fails for any reason, return empty list."""
        from domains.orders.services.orders_service import get_order_shipping_options

        with patch("domains.orders.services.orders_service.compare_shipping_options") as mock_compare:
            mock_compare.side_effect = RuntimeError("unexpected failure")
            order = MagicMock()
            order.warehouse_country = "US"
            order.warehouse_city = "NYC"
            order.total_weight_kg = 1.0
            order.id = 42
            result = get_order_shipping_options(order, {"country": "US", "city": "LA"})
            assert result == []


class TestCustomersModerateReview:
    """Tests for moderate_review provider wiring."""

    def test_moderate_review_calls_sentiment_provider(self):
        """Verify reviews service calls analyze_review with text and rating."""
        from domains.customers.services.reviews_service import moderate_review

        with patch("domains.customers.services.reviews_service.analyze_review") as mock_analyze:
            mock_analyze.return_value = {"combined_score": 0.8, "combined_label": "positive"}
            result = moderate_review("Great product!", 5)
            mock_analyze.assert_called_once_with("Great product!", rating=5)
            assert result["is_positive"] is True
            assert result["needs_review"] is False
            assert result["label"] == "positive"

    def test_moderate_review_flags_negative_sentiment(self):
        """Reviews with strongly negative scores need manual review."""
        from domains.customers.services.reviews_service import moderate_review

        with patch("domains.customers.services.reviews_service.analyze_review") as mock_analyze:
            mock_analyze.return_value = {"combined_score": -0.7, "combined_label": "toxic"}
            result = moderate_review("Terrible experience!", 1)
            assert result["is_positive"] is False
            assert result["needs_review"] is True
            assert result["label"] == "toxic"

    def test_moderate_review_handles_missing_sdk(self):
        """When sentiment SDK not installed, graceful degradation."""
        from domains.customers.services.reviews_service import moderate_review

        with patch("domains.customers.services.reviews_service.analyze_review",
                   side_effect=NotImplementedError("SDK not available")):
            result = moderate_review("Great product!", 5)
            assert result["is_positive"] is True
            assert result["needs_review"] is False
            assert result["label"] == "neutral"

    def test_moderate_review_handles_generic_failure(self):
        """When sentiment analysis raises unexpected error, degrade gracefully."""
        from domains.customers.services.reviews_service import moderate_review

        with patch("domains.customers.services.reviews_service.analyze_review",
                   side_effect=RuntimeError("provider crashed")):
            result = moderate_review("Okay product.", 3)
            assert result["is_positive"] is True
            assert result["needs_review"] is False
            assert result["label"] == "neutral"


class TestCustomersSearchProducts:
    """Tests for search_products provider wiring."""

    def test_search_products_calls_search_engine(self):
        """Verify search_products delegates to AdvancedSearchEngine.search."""
        from domains.customers.services import search_service

        with patch.object(search_service, "_search_engine") as mock_engine:
            mock_engine.search.return_value = {"products": [], "total": 0}
            result = search_service.search_products("shoes", limit=10)
            mock_engine.search.assert_called_once_with(query="shoes", filters=None, limit=10)
            assert "products" in result

    def test_search_products_with_filters(self):
        """Verify filters are passed through to the search engine."""
        from domains.customers.services import search_service

        with patch.object(search_service, "_search_engine") as mock_engine:
            mock_engine.search.return_value = {"products": [{"id": 1}], "total": 1}
            filters = {"category": "fashion", "min_price": 10.0}
            result = search_service.search_products("dress", filters=filters, limit=5)
            mock_engine.search.assert_called_once_with(query="dress", filters=filters, limit=5)
            assert result["total"] == 1

    def test_search_products_handles_connection_error(self):
        """When search provider is unreachable, return empty result with error info."""
        from domains.customers.services import search_service

        with patch.object(search_service, "_search_engine") as mock_engine:
            mock_engine.search.side_effect = ConnectionError("timeout")
            result = search_service.search_products("shoes", limit=10)
            assert result["products"] == []
            assert result["total"] == 0
            assert "error" in result

    def test_load_search_catalog_calls_engine(self):
        """Verify load_search_catalog delegates to engine.load_product_catalog."""
        from domains.customers.services import search_service

        with patch.object(search_service, "_search_engine") as mock_engine:
            mock_engine.load_product_catalog.return_value = 42
            catalog = [{"id": 1, "name": "Sneakers"}]
            result = search_service.load_search_catalog(catalog)
            mock_engine.load_product_catalog.assert_called_once_with(catalog)
            assert result == 42
