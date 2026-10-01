"""Domain tests for catalog — products, categories, and search."""
from __future__ import annotations

import pytest


class TestCatalogServiceImports:
    """Smoke tests: verify catalog service modules are importable."""

    def test_import_catalog_search_service(self):
        from domains.catalog.services.search import search_service

        assert search_service is not None

    def test_import_products_service(self):
        from domains.catalog.services.products import products_service

        assert products_service is not None

    def test_import_category_service(self):
        from domains.catalog.services.categories import category_service

        assert category_service is not None

    def test_import_product_model(self):
        from domains.catalog.models.products import Product

        assert Product is not None

    def test_import_category_model(self):
        from domains.catalog.models.products import Category

        assert Category is not None

    def test_import_catalog_ports(self):
        from domains.catalog.ports import get_banner_by_id, list_banners

        assert callable(get_banner_by_id)
        assert callable(list_banners)

    def test_import_catalog_features(self):
        from domains.catalog.features import CATALOG_FEATURES

        assert isinstance(CATALOG_FEATURES, (list, tuple, set))


class TestProductSearch:
    """Tests for product search functionality."""

    def test_search_service_has_price_keywords(self):
        from domains.catalog.services.search.search_service import PRICE_KEYWORDS

        assert isinstance(PRICE_KEYWORDS, list)
        assert len(PRICE_KEYWORDS) > 0

    def test_search_service_has_category_synonyms(self):
        from domains.catalog.services.search.search_service import CATEGORY_SYNONYMS

        assert isinstance(CATEGORY_SYNONYMS, dict)
        assert "electronics" in CATEGORY_SYNONYMS

    def test_search_service_has_stopwords(self):
        from domains.catalog.services.search.search_service import QUERY_STOPWORDS

        assert isinstance(QUERY_STOPWORDS, set)
        assert "the" in QUERY_STOPWORDS

    def test_product_model_fields(self, db_session):
        from domains.catalog.models.products import Product

        product = Product(
            name="Test Product",
            slug="test-product",
            price=29.99,
            currency="USD",
        )
        db_session.add(product)
        db_session.flush()

        assert product.id is not None
        assert product.name == "Test Product"
        assert product.slug == "test-product"


class TestCategoryTree:
    """Tests for category tree operations."""

    def test_category_tree_compute_path(self):
        from infrastructure.utils.category_tree import compute_category_path

        assert callable(compute_category_path)

    def test_category_tree_chain_for(self):
        from infrastructure.utils.category_tree import _chain_for

        assert callable(_chain_for)

    def test_category_model_fields(self, db_session):
        from domains.catalog.models.products import Category

        category = Category(
            name="Electronics",
            slug="electronics",
            is_active=True,
        )
        db_session.add(category)
        db_session.flush()

        assert category.id is not None
        assert category.name == "Electronics"
        assert category.is_active is True

    def test_category_service_list_categories(self):
        from domains.catalog.services.categories.category_service import list_categories

        assert callable(list_categories)

    def test_category_service_get_category_by_id(self):
        from domains.catalog.services.categories.category_service import get_category_by_id

        assert callable(get_category_by_id)
