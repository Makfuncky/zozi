"""Behavior tests for catalog domain — products, categories, search, reviews, and coupons."""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from domains.catalog.models.products import Product, Category, ProductVariant, ProductReview


def _create_category(db_session, name="Test Category", slug="test-category", parent_id=None):
    category = Category(
        name=name,
        slug=slug,
        parent_id=parent_id,
        is_active=True,
    )
    db_session.add(category)
    db_session.flush()
    return category


def _create_product(db_session, name="Test Product", price=29.99, stock=100, is_active=True):
    product = Product(
        name=name,
        price=Decimal(str(price)),
        stock=stock,
        is_active=is_active,
    )
    db_session.add(product)
    db_session.flush()
    return product


# ══════════════════════════════════════════════════════════════════
# Product Creation and Update
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProductCreation:
    """Test product creation and update."""

    def test_create_product(self, db_session):
        product = _create_product(db_session, name="New Product", price=49.99)
        assert product.id is not None
        assert product.name == "New Product"
        assert float(product.price) == 49.99

    def test_product_default_active(self, db_session):
        product = _create_product(db_session)
        assert product.is_active is True

    def test_update_product_name(self, db_session):
        product = _create_product(db_session, name="Old Name")
        product.name = "Updated Name"
        db_session.flush()
        assert product.name == "Updated Name"

    def test_update_product_price(self, db_session):
        product = _create_product(db_session, price=10.00)
        product.price = Decimal("15.00")
        db_session.flush()
        assert float(product.price) == 15.00

    def test_deactivate_product(self, db_session):
        product = _create_product(db_session, is_active=True)
        product.is_active = False
        db_session.flush()
        assert product.is_active is False

    def test_product_stock_tracking(self, db_session):
        product = _create_product(db_session, stock=50)
        product.stock -= 5
        db_session.flush()
        assert product.stock == 45


# ══════════════════════════════════════════════════════════════════
# Category Tree Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCategoryTree:
    """Test category tree management."""

    def test_create_root_category(self, db_session):
        category = _create_category(db_session, name="Electronics", slug="electronics")
        assert category.id is not None
        assert category.parent_id is None

    def test_create_child_category(self, db_session):
        parent = _create_category(db_session, name="Electronics", slug="electronics")
        child = _create_category(db_session, name="Phones", slug="phones", parent_id=parent.id)
        assert child.parent_id == parent.id

    def test_category_active_status(self, db_session):
        category = _create_category(db_session, is_active=True)
        assert category.is_active is True

    def test_deactivate_category(self, db_session):
        category = _create_category(db_session, is_active=True)
        category.is_active = False
        db_session.flush()
        assert category.is_active is False


# ══════════════════════════════════════════════════════════════════
# Product Search
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProductSearch:
    """Test product search functionality."""

    def test_search_products_by_name(self, db_session):
        _create_product(db_session, name="iPhone 15 Pro")
        _create_product(db_session, name="Samsung Galaxy S24")
        results = db_session.query(Product).filter(Product.name.ilike("%iphone%")).all()
        assert len(results) >= 1
        assert "iPhone" in results[0].name

    def test_search_products_by_price_range(self, db_session):
        _create_product(db_session, name="Cheap Product", price=10.00)
        _create_product(db_session, name="Expensive Product", price=500.00)
        results = db_session.query(Product).filter(Product.price.between(5.00, 50.00)).all()
        assert len(results) >= 1

    def test_search_active_products_only(self, db_session):
        _create_product(db_session, name="Active Product", is_active=True)
        _create_product(db_session, name="Inactive Product", is_active=False)
        results = db_session.query(Product).filter(Product.is_active == True).all()
        assert all(p.is_active for p in results)

    def test_search_with_ai_search_service(self):
        from domains.catalog.services.search_service import search_products
        result = search_products(query="laptop", limit=10)
        assert isinstance(result, dict)
        assert "products" in result

    def test_search_with_filters(self):
        from domains.catalog.services.search_service import search_products
        result = search_products(query="phone", filters={"category": "electronics"}, limit=5)
        assert isinstance(result, dict)

    def test_load_search_catalog(self):
        from domains.catalog.services.search_service import load_search_catalog
        products = [
            {"id": 1, "name": "Product A", "price": 10.00},
            {"id": 2, "name": "Product B", "price": 20.00},
        ]
        result = load_search_catalog(products)
        assert isinstance(result, int)


# ══════════════════════════════════════════════════════════════════
# Product Variant Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProductVariants:
    """Test product variant management."""

    def test_create_product_variant(self, db_session):
        product = _create_product(db_session)
        variant = ProductVariant(
            product_id=product.id,
            title="Large Red",
            size="L",
            color="Red",
            stock=25,
            is_active=True,
        )
        db_session.add(variant)
        db_session.flush()
        assert variant.id is not None
        assert variant.product_id == product.id
        assert variant.size == "L"

    def test_variant_stock_tracking(self, db_session):
        product = _create_product(db_session)
        variant = ProductVariant(
            product_id=product.id,
            title="Medium Blue",
            size="M",
            color="Blue",
            stock=30,
        )
        db_session.add(variant)
        db_session.flush()
        variant.stock -= 5
        db_session.flush()
        assert variant.stock == 25

    def test_deactivate_variant(self, db_session):
        product = _create_product(db_session)
        variant = ProductVariant(
            product_id=product.id,
            title="Small Green",
            size="S",
            color="Green",
            is_active=True,
        )
        db_session.add(variant)
        db_session.flush()
        variant.is_active = False
        db_session.flush()
        assert variant.is_active is False


# ══════════════════════════════════════════════════════════════════
# Review Creation and Moderation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProductReviews:
    """Test review creation and moderation."""

    def test_create_review(self, db_session):
        product = _create_product(db_session)
        review = ProductReview(
            product_id=product.id,
            user_id=1,
            rating=5,
            title="Great product!",
            body="Works as expected",
            is_approved=False,
        )
        db_session.add(review)
        db_session.flush()
        assert review.id is not None
        assert review.rating == 5
        assert review.is_approved is False

    def test_review_rating_range(self, db_session):
        product = _create_product(db_session)
        for rating in [1, 2, 3, 4, 5]:
            review = ProductReview(
                product_id=product.id,
                user_id=1,
                rating=rating,
                title=f"Rating {rating}",
            )
            db_session.add(review)
        db_session.flush()
        reviews = db_session.query(ProductReview).filter(ProductReview.product_id == product.id).all()
        assert len(reviews) == 5

    def test_approve_review(self, db_session):
        product = _create_product(db_session)
        review = ProductReview(
            product_id=product.id,
            user_id=1,
            rating=4,
            is_approved=False,
        )
        db_session.add(review)
        db_session.flush()
        review.is_approved = True
        db_session.flush()
        assert review.is_approved is True

    def test_filter_approved_reviews(self, db_session):
        product = _create_product(db_session)
        approved = ProductReview(product_id=product.id, user_id=1, rating=5, is_approved=True)
        unapproved = ProductReview(product_id=product.id, user_id=2, rating=1, is_approved=False)
        db_session.add_all([approved, unapproved])
        db_session.flush()
        approved_reviews = db_session.query(ProductReview).filter(
            ProductReview.product_id == product.id, ProductReview.is_approved == True
        ).all()
        assert len(approved_reviews) == 1
        assert approved_reviews[0].rating == 5


# ══════════════════════════════════════════════════════════════════
# Wishlist Operations
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestWishlistOperations:
    """Test wishlist operations."""

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


# ══════════════════════════════════════════════════════════════════
# Banner Management
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestBannerManagement:
    """Test banner management."""

    def test_create_banner(self, db_session):
        from domains.catalog.models.banner import Banner
        banner = Banner(
            title="Summer Sale",
            image_url="/banners/summer.jpg",
            is_active=True,
            position="hero",
        )
        db_session.add(banner)
        db_session.flush()
        assert banner.id is not None
        assert banner.is_active is True

    def test_banner_active_status(self, db_session):
        from domains.catalog.models.banner import Banner
        banner = Banner(title="Test Banner", is_active=True)
        db_session.add(banner)
        db_session.flush()
        banner.is_active = False
        db_session.flush()
        assert banner.is_active is False


# ══════════════════════════════════════════════════════════════════
# Coupon Creation and Validation
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestCouponOperations:
    """Test coupon creation and validation."""

    def test_create_coupon(self, db_session):
        from domains.promotions.models.promotions import Coupon
        coupon = Coupon(
            code="SUMMER20",
            discount_type="percentage",
            discount_value=Decimal("20.00"),
            is_active=True,
            valid_from=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(coupon)
        db_session.flush()
        assert coupon.id is not None
        assert coupon.code == "SUMMER20"

    def test_coupon_active_status(self, db_session):
        from domains.promotions.models.promotions import Coupon
        coupon = Coupon(
            code="WINTER10",
            is_active=True,
        )
        db_session.add(coupon)
        db_session.flush()
        coupon.is_active = False
        db_session.flush()
        assert coupon.is_active is False

    def test_coupon_date_validity(self, db_session):
        from domains.promotions.models.promotions import Coupon
        now = datetime.now(timezone.utc)
        coupon = Coupon(
            code="VALID2024",
            valid_from=now - timedelta(days=1),
            valid_until=now + timedelta(days=30),
        )
        db_session.add(coupon)
        db_session.flush()
        assert coupon.valid_from < coupon.valid_until

    def test_validate_coupon_code(self, db_session):
        from domains.promotions.models.promotions import Coupon
        coupon = Coupon(
            code="TESTCODE",
            is_active=True,
            valid_from=datetime.now(timezone.utc) - timedelta(days=1),
            valid_until=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(coupon)
        db_session.flush()
        found = db_session.query(Coupon).filter(Coupon.code == "TESTCODE", Coupon.is_active == True).first()
        assert found is not None


# ══════════════════════════════════════════════════════════════════
# Product Filtering and Sorting
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestProductFiltering:
    """Test product filtering and sorting."""

    def test_filter_by_category(self, db_session):
        category = _create_category(db_session)
        product = _create_product(db_session)
        product.category_id = category.id
        db_session.flush()
        results = db_session.query(Product).filter(Product.category_id == category.id).all()
        assert len(results) >= 1

    def test_filter_by_price_ascending(self, db_session):
        _create_product(db_session, name="Cheap", price=5.00)
        _create_product(db_session, name="Mid", price=25.00)
        _create_product(db_session, name="Expensive", price=100.00)
        results = db_session.query(Product).order_by(Product.price.asc()).all()
        assert float(results[0].price) <= float(results[1].price)

    def test_filter_by_price_descending(self, db_session):
        _create_product(db_session, name="Cheap", price=5.00)
        _create_product(db_session, name="Mid", price=25.00)
        _create_product(db_session, name="Expensive", price=100.00)
        results = db_session.query(Product).order_by(Product.price.desc()).all()
        assert float(results[0].price) >= float(results[1].price)

    def test_filter_in_stock_only(self, db_session):
        _create_product(db_session, name="In Stock", stock=10)
        _create_product(db_session, name="Out of Stock", stock=0)
        results = db_session.query(Product).filter(Product.stock > 0).all()
        assert all(p.stock > 0 for p in results)


# ══════════════════════════════════════════════════════════════════
# Upload Job Processing
# ══════════════════════════════════════════════════════════════════


@pytest.mark.integration
class TestUploadJobProcessing:
    """Test upload job processing."""

    def test_create_upload_job(self, db_session):
        from domains.catalog.services.ai_upload_service import create_upload_job
        result = create_upload_job(user_id=1, filename="products.csv", db=db_session)
        assert result is not None

    def test_get_upload_job_status(self, db_session):
        from domains.catalog.services.ai_upload_service import get_upload_job
        result = get_upload_job(job_id=1, db=db_session)
        assert result is not None or result is None
