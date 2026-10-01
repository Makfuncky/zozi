"""Tests for FILE-54 resolution: keyset pagination, message constants, listing consolidation."""
from __future__ import annotations

import inspect
from unittest.mock import MagicMock, patch

import pytest

from domains.catalog.services.products.products_service import (
    MODERATION_APPROVE_MESSAGE,
    MODERATION_REJECT_MESSAGE,
    get_products,
    list_my_products,
    list_products,
    list_products_paginated,
)


class TestModerationMessages:
    def test_approve_message_constant(self):
        assert MODERATION_APPROVE_MESSAGE == "Product approved"

    def test_reject_message_constant(self):
        assert MODERATION_REJECT_MESSAGE == "Product rejected"

    def test_approve_product_by_id_uses_constant(self):
        from domains.catalog.services.products import products_service as svc

        source = inspect.getsource(svc.approve_product_by_id)
        assert "MODERATION_APPROVE_MESSAGE" in source
        assert '"Product approved"' not in source

    def test_reject_product_by_id_uses_constant(self):
        from domains.catalog.services.products import products_service as svc

        source = inspect.getsource(svc.reject_product_by_id)
        assert "MODERATION_REJECT_MESSAGE" in source
        assert '"Product rejected"' not in source


class TestListProductsSignature:
    def test_list_products_accepts_cursor(self):
        sig = inspect.signature(list_products)
        assert "cursor" in sig.parameters

    def test_list_products_returns_dict(self):
        db = MagicMock()
        result = list_products(db, limit=10)
        assert isinstance(result, dict)
        assert "items" in result
        assert "total" in result


class TestGetProductsDelegates:
    def test_get_products_delegates_to_list_products(self):
        source = inspect.getsource(get_products)
        assert "list_products(" in source
        assert "result[" in source


class TestListProductsPaginatedDelegates:
    def test_list_products_paginated_delegates_to_list_products(self):
        source = inspect.getsource(list_products_paginated)
        assert "list_products(" in source


class TestListMyProductsDelegates:
    def test_list_my_products_delegates_to_list_products(self):
        source = inspect.getsource(list_my_products)
        assert "list_products(" in source
