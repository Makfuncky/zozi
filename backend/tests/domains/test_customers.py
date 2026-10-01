"""Domain tests for customers — cart, wishlist, and profile operations."""
from __future__ import annotations

import pytest


class TestCustomerServiceImports:
    """Smoke tests: verify customer service modules are importable."""

    def test_import_cart_service(self):
        from domains.customers.services import cart_service

        assert cart_service is not None

    def test_import_wishlist_service(self):
        from domains.customers.services import wishlist_service

        assert wishlist_service is not None

    def test_import_profile_service(self):
        from domains.customers.services import profile_service

        assert profile_service is not None

    def test_import_customer_models(self):
        from domains.customers.models.customer_schema_models import CartItem

        assert CartItem is not None

    def test_import_customer_events(self):
        from domains.customers.events import CustomerRegisteredEvent

        assert CustomerRegisteredEvent is not None

    def test_import_customer_ports(self):
        from domains.customers.ports import get_customer_by_id

        assert callable(get_customer_by_id)

    def test_import_customer_features(self):
        from domains.customers.features import CUSTOMER_FEATURES

        assert isinstance(CUSTOMER_FEATURES, (list, tuple, set))


class TestCartOperations:
    """Tests for cart service operations."""

    def test_cart_service_has_get_cart(self):
        from domains.customers.services.cart_service import get_cart_items

        assert callable(get_cart_items)

    def test_cart_service_has_add_to_cart(self):
        from domains.customers.services.cart_service import add_to_cart

        assert callable(add_to_cart)

    def test_cart_service_has_remove_from_cart(self):
        from domains.customers.services.cart_service import remove_from_cart

        assert callable(remove_from_cart)

    def test_cart_item_model_fields(self, db_session):
        from domains.customers.models.customer_schema_models import CartItem

        cart_item = CartItem(
            user_id=1,
            product_id=1,
            quantity=1,
        )
        db_session.add(cart_item)
        db_session.flush()

        assert cart_item.id is not None
        assert cart_item.user_id == 1
        assert cart_item.product_id == 1
        assert cart_item.quantity == 1


class TestWishlistOperations:
    """Tests for wishlist service operations."""

    def test_wishlist_service_has_get_user_wishlist(self):
        from domains.customers.services.wishlist_service import get_user_wishlist

        assert callable(get_user_wishlist)

    def test_wishlist_service_has_add_to_wishlist(self):
        from domains.customers.services.wishlist_service import add_to_wishlist

        assert callable(add_to_wishlist)

    def test_wishlist_service_has_remove_from_wishlist(self):
        from domains.customers.services.wishlist_service import remove_from_wishlist

        assert callable(remove_from_wishlist)

    def test_wishlist_read_service_exists(self):
        from domains.customers.services.wishlist_read_service import get_user_wishlist

        assert callable(get_user_wishlist)

    def test_wishlist_write_service_exists(self):
        from domains.customers.services.wishlist_write_service import create_wishlist_item, delete_wishlist_item

        assert callable(create_wishlist_item)
        assert callable(delete_wishlist_item)
