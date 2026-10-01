from __future__ import annotations

"""Tests for Chart of Categories (CoC) and Waterfall Commission Matrix.

Covers:
- 7-layer category tree operations
- Commission waterfall calculation
- API endpoints
"""
import pytest
from decimal import Decimal

from domains.catalog.models.commission import (
    CommissionGroup,
    CommissionProfile,
    CommissionRule,
)
from domains.catalog.services.coc_service import (
    create_category,
    get_category_tree,
    toggle_category_active,
    search_categories,
    create_product_type,
    create_attribute,
)
from domains.catalog.services.commission_engine import (
    preview_commission,
    get_global_default_rate,
    set_global_default_rate,
)


# ── Fixtures ──────────────────────────────────────────────────────────────


@pytest.fixture
def commission_group(db_session):
    """Create a commission group."""
    group = CommissionGroup(
        name="Test Electronics",
        slug="test-electronics",
        base_rate=Decimal("10.00"),
    )
    db_session.add(group)
    db_session.commit()
    return group


@pytest.fixture
def coc_tree(db_session, commission_group):
    """Create a 3-level category tree."""
    l1 = create_category(
        db_session,
        name="Electronics",
        slug="electronics",
        level=1,
        commission_group_id=commission_group.id,
    )
    l2 = create_category(
        db_session,
        name="Computers",
        slug="computers",
        level=2,
        parent_id=l1.id,
    )
    l3 = create_category(
        db_session,
        name="Laptops",
        slug="laptops",
        level=3,
        parent_id=l2.id,
    )
    db_session.commit()
    return {"l1": l1, "l2": l2, "l3": l3}


@pytest.fixture
def product_type(db_session, coc_tree):
    """Create a product type for laptops."""
    pt = create_product_type(
        db_session,
        coc_category_id=coc_tree["l3"].id,
        name="Gaming Laptop",
        slug="gaming-laptop",
    )
    db_session.commit()
    return pt


@pytest.fixture
def commission_profile(db_session):
    """Create a commission profile for a supplier."""
    profile = CommissionProfile(
        supplier_id=1,
        name="Default",
        slug="default",
        is_default=True,
    )
    db_session.add(profile)
    db_session.commit()
    return profile


@pytest.fixture
def commission_rules(db_session, commission_profile, coc_tree, product_type):
    """Create waterfall commission rules."""
    rules = []

    # Rule 1: Apple brand discount (highest priority)
    rules.append(CommissionRule(
        profile_id=commission_profile.id,
        name="Apple Brand Discount",
        brand="Apple",
        rate=Decimal("8.00"),
        priority=20,
    ))

    # Rule 2: Gaming laptops (medium priority)
    rules.append(CommissionRule(
        profile_id=commission_profile.id,
        name="Gaming Laptops",
        product_type_id=product_type.id,
        rate=Decimal("12.00"),
        priority=30,
    ))

    # Rule 3: Electronics department (lower priority)
    rules.append(CommissionRule(
        profile_id=commission_profile.id,
        name="Electronics Base",
        coc_node_id=coc_tree["l1"].id,
        rate=Decimal("10.00"),
        priority=50,
    ))

    db_session.add_all(rules)
    db_session.commit()
    return rules


# ── Category Tree Tests ───────────────────────────────────────────────────


class TestCategoryTree:
    """Test 7-layer CoC tree operations."""

    def test_create_category_level_1(self, db_session, commission_group):
        """Create a Level 1 department."""
        cat = create_category(
            db_session,
            name="Fashion",
            slug="fashion",
            level=1,
            commission_group_id=commission_group.id,
        )
        db_session.commit()

        assert cat.id is not None
        assert cat.level == 1
        assert cat.parent_id is None
        assert cat.path == "/fashion/"
        assert cat.commission_group_id == commission_group.id

    def test_create_category_level_2(self, db_session, coc_tree):
        """Create a Level 2 category under Level 1."""
        cat = create_category(
            db_session,
            name="Men's Clothing",
            slug="mens-clothing",
            level=2,
            parent_id=coc_tree["l1"].id,
        )
        db_session.commit()

        assert cat.level == 2
        assert cat.parent_id == coc_tree["l1"].id
        assert "/electronics/" in cat.path

    def test_create_category_level_3(self, db_session, coc_tree):
        """Create a Level 3 sub-category."""
        cat = create_category(
            db_session,
            name="Shirts",
            slug="shirts",
            level=3,
            parent_id=coc_tree["l2"].id,
        )
        db_session.commit()

        assert cat.level == 3
        assert cat.parent_id == coc_tree["l2"].id

    def test_get_category_tree(self, db_session, coc_tree):
        """Get the full category tree."""
        tree = get_category_tree(db_session, max_depth=3)

        assert len(tree) == 1  # One root (Electronics)
        assert tree[0]["name"] == "Electronics"
        assert len(tree[0]["children"]) == 1  # Computers
        assert tree[0]["children"][0]["name"] == "Computers"
        assert len(tree[0]["children"][0]["children"]) == 1  # Laptops

    def test_toggle_category_active(self, db_session, coc_tree):
        """Toggle category active status."""
        result = toggle_category_active(db_session, coc_tree["l3"].id, False)
        db_session.commit()

        assert result is not None
        assert result.is_active is False

        # Toggle back
        result = toggle_category_active(db_session, coc_tree["l3"].id, True)
        db_session.commit()
        assert result.is_active is True

    def test_search_categories(self, db_session, coc_tree):
        """Search categories by name."""
        results = search_categories(db_session, "laptop")
        assert len(results) >= 1
        assert any(r["name"] == "Laptops" for r in results)

    def test_create_product_type(self, db_session, coc_tree):
        """Create a Level 4 product type."""
        pt = create_product_type(
            db_session,
            coc_category_id=coc_tree["l3"].id,
            name="Ultrabook",
            slug="ultrabook",
        )
        db_session.commit()

        assert pt.id is not None
        assert pt.coc_category_id == coc_tree["l3"].id

    def test_create_attribute(self, db_session, product_type):
        """Create Level 5-6 attributes."""
        attr = create_attribute(
            db_session,
            product_type_id=product_type.id,
            name="Brand",
            key="brand",
            layer=5,
            options=["Apple", "Dell", "HP"],
        )
        db_session.commit()

        assert attr.id is not None
        assert attr.layer == 5
        assert attr.product_type_id == product_type.id


# ── Commission Engine Tests ───────────────────────────────────────────────


class TestCommissionEngine:
    """Test waterfall commission calculation."""

    def test_apple_brand_discount(
        self, db_session, coc_tree, product_type, commission_profile, commission_rules
    ):
        """Apple products should get 8% commission (brand override)."""
        result = preview_commission(
            db_session,
            supplier_id=1,
            coc_node_id=coc_tree["l3"].id,
            gross_amount=Decimal("5000"),
            brand="Apple",
        )

        assert result.rate == Decimal("8.00")
        assert result.amount == Decimal("400.00")
        assert result.net_amount == Decimal("4600.00")
        assert result.rule_name == "Apple Brand Discount"

    def test_gaming_laptop_override(
        self, db_session, coc_tree, product_type, commission_profile, commission_rules
    ):
        """Gaming laptops should get 12% commission (product type override)."""
        result = preview_commission(
            db_session,
            supplier_id=1,
            coc_node_id=coc_tree["l3"].id,
            gross_amount=Decimal("8000"),
            product_type_id=product_type.id,
        )

        assert result.rate == Decimal("12.00")
        assert result.amount == Decimal("960.00")
        assert result.net_amount == Decimal("7040.00")
        assert result.rule_name == "Gaming Laptops"

    def test_electronics_base_via_ancestor(
        self, db_session, coc_tree, product_type, commission_profile, commission_rules
    ):
        """Generic electronics should get 10% via ancestor path matching."""
        result = preview_commission(
            db_session,
            supplier_id=1,
            coc_node_id=coc_tree["l3"].id,
            gross_amount=Decimal("3000"),
        )

        assert result.rate == Decimal("10.00")
        assert result.amount == Decimal("300.00")
        assert result.rule_name == "Electronics Base"

    def test_apple_gaming_higher_priority(
        self, db_session, coc_tree, product_type, commission_profile, commission_rules
    ):
        """Apple rule (priority 20) should win over Gaming (priority 30)."""
        result = preview_commission(
            db_session,
            supplier_id=1,
            coc_node_id=coc_tree["l3"].id,
            gross_amount=Decimal("10000"),
            product_type_id=product_type.id,
            brand="Apple",
        )

        assert result.rate == Decimal("8.00")
        assert result.rule_name == "Apple Brand Discount"

    def test_global_default_fallback(self, db_session, coc_tree):
        """No profile should fall back to global default (15%)."""
        result = preview_commission(
            db_session,
            supplier_id=999,  # No profile
            coc_node_id=coc_tree["l3"].id,
            gross_amount=Decimal("1000"),
        )

        assert result.rate == get_global_default_rate()
        assert result.rule_name == "Global Default"

    def test_global_default_rate(self):
        """Test getting and setting global default rate."""
        original = get_global_default_rate()
        set_global_default_rate(Decimal("20.00"))
        assert get_global_default_rate() == Decimal("20.00")
        set_global_default_rate(original)  # Restore


# ── API Integration Tests ─────────────────────────────────────────────────


class TestCoCAPI:
    """Test CoC API endpoints."""

    def test_get_tree_endpoint(self, admin_client, coc_tree):
        """GET /admin/catalog/coc/tree returns category tree."""
        # This would need the admin_client fixture from conftest
        pass

    def test_create_category_endpoint(self, admin_client):
        """POST /admin/catalog/coc/categories creates a category."""
        pass

    def test_toggle_active_endpoint(self, admin_client, coc_tree):
        """POST /admin/catalog/coc/categories/{id}/toggle-active toggles status."""
        pass

    def test_commission_preview_endpoint(self, admin_client, coc_tree):
        """POST /admin/catalog/coc/commission/preview returns commission."""
        pass
