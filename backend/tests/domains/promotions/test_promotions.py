"""Tests for promotions domain: promotions, flash sales, and admin operations."""
from __future__ import annotations

import pytest


@pytest.mark.integration
def test_create_promotion_validates_dates(db_session):
    """Promotion start date must be before end date."""
    pytest.skip("Implement promotion date validation test")


@pytest.mark.integration
def test_flash_sale_write_service_creates_sale(db_session):
    """Flash sale creation should persist and return the sale record."""
    pytest.skip("Implement flash sale creation test")


@pytest.mark.integration
def test_promotion_admin_service_lists_active_promotions(db_session):
    """Admin promotion service should filter by active status."""
    pytest.skip("Implement admin promotion listing test")


@pytest.mark.integration
def test_promotion_events_emit_on_creation(db_session):
    """Creating a promotion should emit a domain event."""
    pytest.skip("Implement promotion event emission test")
