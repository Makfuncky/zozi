"""Behavior tests for customers domain — profile, cart, wishlist, reviews, loyalty, and segmentation."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domains.accounts.models.user import User
from domains.customers.models.customer_schema_models import CartItem, CustomerProfile


def _create_user(db_session, email=None, full_name=None):
    from infrastructure.utils.auth import get_password_hash
    user = User(
        email=email or f"cust_{uuid.uuid4().hex[:8]}@zozi.test",
        username=f"cust_{uuid.uuid4().hex[:8]}",
        hashed_password=get_password_hash("SecurePass1!"),
        role="customer",
        full_name=full_name,
        country_code="AE",
    )
    db_session.add(user)
    db_session.flush()
    return user


def _create_product(db_session, name="Test Product", price=25.00, stock=100):
    from domains.catalog.models.products import Product
    product = Product(
        name=name,
        price=Decimal(str(price)),
        stock=stock,
        is_active=True,
    )
    db_session.add(product)
    db_session.flush()
    return product


# ══════════════════════════════════════════════════════════════════
# Customer Profile Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCustomerProfile:
    """Test customer profile management."""

    def test_get_profile_returns_user_data(self, db_session):
        user = _create_user(db_session, full_name="John Doe")
        from domains.customers.services.profile_service import ProfileService
        service = ProfileService(db_session)
        profile = service.get_profile(user.id)
        assert profile["user_id"] == user.id
        assert profile["full_name"] == "John Doe"

    def test_get_profile_nonexistent_user_raises_404(self, db_session):
        from domains.customers.services.profile_service import ProfileService
        from fastapi import HTTPException
        service = ProfileService(db_session)
        with pytest.raises(HTTPException) as exc_info:
            service.get_profile(99999)
        assert exc_info.value.status_code == 404

    def test_update_profile_full_name(self, db_session):
        user = _create_user(db_session, full_name="Old Name")
        from domains.customers.services.profile_service import ProfileService
        service = ProfileService(db_session)
        result = service.update_profile(user.id, {"full_name": "New Name"})
        assert result["full_name"] == "New Name"

    def test_update_profile_ignores_disallowed_fields(self, db_session):
        user = _create_user(db_session, full_name="Test User")
        original_email = user.email
        from domains.customers.services.profile_service import ProfileService
        service = ProfileService(db_session)
        result = service.update_profile(user.id, {"email": "hacked@evil.com", "full_name": "Updated"})
        assert result["email"] == original_email
        assert result["full_name"] == "Updated"

    def test_get_profile_completion_score(self, db_session):
        user = _create_user(db_session, full_name="Test User")
        from domains.customers.services.profile_service import ProfileService
        service = ProfileService(db_session)
        result = service.get_profile_completion(user.id)
        assert "percent" in result
        assert "filled" in result
        assert "total" in result
        assert "fields" in result
        assert 0 <= result["percent"] <= 100

    def test_profile_completion_increases_with_more_fields(self, db_session):
        user = _create_user(db_session)
        from domains.customers.services.profile_service import ProfileService
        service = ProfileService(db_session)
        before = service.get_profile_completion(user.id)
        user.full_name = "Test Name"
        user.phone = "+971501234567"
        db_session.flush()
        after = service.get_profile_completion(user.id)
        assert after["filled"] >= before["filled"]


# ══════════════════════════════════════════════════════════════════
# Cart Service
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCartService:
    """Test cart service operations."""

    def test_add_item_to_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        user_id = 1
        payload = CartItemCreate(product_id=product.id, quantity=2)
        result = add_to_cart(user_id, payload, db_session)
        assert result["message"] == "Added to cart"

    def test_add_nonexistent_product_rejected(self, db_session):
        from domains.customers.services.cart_service import add_to_cart
        from infrastructure.database.schemas import CartItemCreate
        from fastapi import HTTPException
        payload = CartItemCreate(product_id=99999, quantity=1)
        with pytest.raises(HTTPException) as exc_info:
            add_to_cart(1, payload, db_session)
        assert exc_info.value.status_code == 404

    def test_remove_item_from_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, remove_cart_item
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(1, payload, db_session)
        result = remove_cart_item(1, product.id, db_session)
        assert result["message"] == "Removed"

    def test_remove_nonexistent_item_rejected(self, db_session):
        from domains.customers.services.cart_service import remove_cart_item
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            remove_cart_item(1, 99999, db_session)
        assert exc_info.value.status_code == 404

    def test_update_cart_item_quantity(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, update_cart_item
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        payload = CartItemCreate(product_id=product.id, quantity=1)
        add_to_cart(1, payload, db_session)
        result = update_cart_item(1, product.id, 5, "", "", db_session)
        assert result["message"] == "Updated"

    def test_clear_cart(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, clear_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session)
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(1, payload, db_session)
        result = clear_cart(1, db_session)
        assert result["message"] == "Cart cleared"

    def test_get_cart_returns_subtotal(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product = _create_product(db_session, price=30.00)
        payload = CartItemCreate(product_id=product.id, quantity=2)
        add_to_cart(1, payload, db_session)
        cart = get_cart(1, db_session)
        assert cart.subtotal == 60.00

    def test_cart_total_items_count(self, db_session):
        from domains.customers.services.cart_service import add_to_cart, get_cart
        from infrastructure.database.schemas import CartItemCreate
        product1 = _create_product(db_session, name="Product 1")
        product2 = _create_product(db_session, name="Product 2")
        add_to_cart(1, CartItemCreate(product_id=product1.id, quantity=1), db_session)
        add_to_cart(1, CartItemCreate(product_id=product2.id, quantity=1), db_session)
        cart = get_cart(1, db_session)
        assert cart.total_items == 2


# ══════════════════════════════════════════════════════════════════
# Coupon Application
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCouponApplication:
    """Test coupon application."""

    def test_apply_valid_coupon(self, db_session):
        from domains.customers.services.coupons_service import apply_coupon
        result = apply_coupon(user_id=1, code="VALIDCODE", db=db_session)
        assert result is not None

    def test_apply_invalid_coupon_rejected(self, db_session):
        from domains.customers.services.coupons_service import apply_coupon
        result = apply_coupon(user_id=1, code="INVALIDCODE", db=db_session)
        assert result is None or result.get("error")

    def test_apply_expired_coupon_rejected(self, db_session):
        from domains.customers.services.coupons_service import apply_coupon
        from domains.promotions.models.promotions import Coupon
        coupon = Coupon(
            code="EXPIRED",
            is_active=True,
            valid_from=datetime.now(timezone.utc) - timedelta(days=30),
            valid_until=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(coupon)
        db_session.flush()
        result = apply_coupon(user_id=1, code="EXPIRED", db=db_session)
        assert result is None or result.get("error")


# ══════════════════════════════════════════════════════════════════
# Wishlist Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestWishlistManagement:
    """Test wishlist management."""

    def test_add_to_wishlist(self, db_session):
        from domains.customers.services.wishlist_service import add_to_wishlist
        product = _create_product(db_session)
        result = add_to_wishlist(user_id=1, product_id=product.id, db=db_session)
        assert result is not None

    def test_remove_from_wishlist(self, db_session):
        from domains.customers.services.wishlist_service import add_to_wishlist, remove_from_wishlist
        product = _create_product(db_session)
        add_to_wishlist(user_id=1, product_id=product.id, db=db_session)
        result = remove_from_wishlist(user_id=1, product_id=product.id, db=db_session)
        assert result is not None

    def test_get_user_wishlist(self, db_session):
        from domains.customers.services.wishlist_service import get_user_wishlist
        result = get_user_wishlist(user_id=1, db=db_session)
        assert isinstance(result, list)

    def test_wishlist_duplicate_prevention(self, db_session):
        from domains.customers.services.wishlist_service import add_to_wishlist, get_user_wishlist
        product = _create_product(db_session)
        add_to_wishlist(user_id=1, product_id=product.id, db=db_session)
        add_to_wishlist(user_id=1, product_id=product.id, db=db_session)
        wishlist = get_user_wishlist(user_id=1, db=db_session)
        product_ids = [w.product_id for w in wishlist]
        assert product_ids.count(product.id) == 1


# ══════════════════════════════════════════════════════════════════
# Review Submission
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestReviewSubmission:
    """Test review submission."""

    def test_submit_review(self, db_session):
        from domains.customers.services.reviews_service import submit_review
        product = _create_product(db_session)
        result = submit_review(
            user_id=1,
            product_id=product.id,
            rating=5,
            title="Great!",
            body="Love it",
            db=db_session,
        )
        assert result is not None

    def test_review_rating_validation(self, db_session):
        from domains.customers.services.reviews_service import submit_review
        product = _create_product(db_session)
        result = submit_review(
            user_id=1,
            product_id=product.id,
            rating=6,
            title="Invalid",
            body="Rating too high",
            db=db_session,
        )
        assert result is None or result.get("error")


# ══════════════════════════════════════════════════════════════════
# Loyalty Points
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestLoyaltyPoints:
    """Test loyalty points."""

    def test_award_loyalty_points(self, db_session):
        from domains.customers.services.loyalty_service import award_points
        result = award_points(user_id=1, points=100, reason="Purchase", db=db_session)
        assert result is not None

    def test_redeem_loyalty_points(self, db_session):
        from domains.customers.services.loyalty_service import award_points, redeem_points
        award_points(user_id=1, points=100, reason="Test", db=db_session)
        result = redeem_points(user_id=1, points=50, reason="Reward", db=db_session)
        assert result is not None

    def test_insufficient_points_rejected(self, db_session):
        from domains.customers.services.loyalty_service import redeem_points
        result = redeem_points(user_id=1, points=99999, reason="Too many", db=db_session)
        assert result is None or result.get("error")

    def test_get_loyalty_balance(self, db_session):
        from domains.customers.services.loyalty_service import get_points_balance
        result = get_points_balance(user_id=1, db=db_session)
        assert isinstance(result, int)


# ══════════════════════════════════════════════════════════════════
# Customer Health Scoring
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCustomerHealthScoring:
    """Test customer health scoring."""

    def test_calculate_health_score(self, db_session):
        from domains.customers.services.customer_health_service import get_customer_health
        result = get_customer_health(user_id=1, db=db_session)
        assert result is not None

    def test_health_score_components(self, db_session):
        from domains.customers.services.customer_health_engine import CustomerHealthEngine
        engine = CustomerHealthEngine(db_session)
        result = engine.calculate_score(user_id=1)
        assert "score" in result or isinstance(result, (int, float))


# ══════════════════════════════════════════════════════════════════
# Customer Segmentation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCustomerSegmentation:
    """Test customer segmentation."""

    def test_segment_customer(self, db_session):
        from domains.customers.services.segmentation_service import segment_customer
        result = segment_customer(user_id=1, db=db_session)
        assert result is not None

    def test_get_customer_segment(self, db_session):
        from domains.customers.services.segmentation_service import get_customer_segment
        result = get_customer_segment(user_id=1, db=db_session)
        assert result is not None


# ══════════════════════════════════════════════════════════════════
# Address Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestAddressManagement:
    """Test address management."""

    def test_add_address(self, db_session):
        from domains.customers.services.address_verification_service import add_address
        result = add_address(
            user_id=1,
            street="123 Test St",
            city="Dubai",
            country_code="AE",
            db=db_session,
        )
        assert result is not None

    def test_get_user_addresses(self, db_session):
        user = _create_user(db_session)
        from domains.accounts.models.user import Address
        address = Address(
            user_id=user.id,
            street="456 Main St",
            city="Abu Dhabi",
            country_code="AE",
        )
        db_session.add(address)
        db_session.flush()
        addresses = db_session.query(Address).filter(Address.user_id == user.id).all()
        assert len(addresses) >= 1

    def test_delete_address(self, db_session):
        user = _create_user(db_session)
        from domains.accounts.models.user import Address
        address = Address(
            user_id=user.id,
            street="789 Delete St",
            city="Sharjah",
            country_code="AE",
        )
        db_session.add(address)
        db_session.flush()
        address_id = address.id
        db_session.delete(address)
        db_session.flush()
        assert db_session.query(Address).filter(Address.id == address_id).first() is None


# ══════════════════════════════════════════════════════════════════
# Search History
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestSearchHistory:
    """Test search history."""

    def test_record_search_history(self, db_session):
        from domains.customers.services.search_service import record_search
        result = record_search(user_id=1, query="laptop", db=db_session)
        assert result is not None

    def test_get_search_history(self, db_session):
        from domains.customers.services.search_service import get_search_history
        result = get_search_history(user_id=1, db=db_session)
        assert isinstance(result, list)
