"""Tests for AIDRIFT-017: verify unused _ parameters are removed from admin_products_service."""
from __future__ import annotations

import inspect

import pytest


MODULE_PATH = "domains.catalog.services.products.admin_products_service"


@pytest.fixture
def admin_products_service():
    import importlib

    return importlib.import_module(MODULE_PATH)


class TestAidrift017UnusedUnderscoreRemoved:
    """Verify the 11 functions no longer accept an unused _ parameter."""

    FUNCTIONS_WITH_FORMER_UNUSED_UNDERSCORE = [
        "list_all_products",
        "approve_product",
        "reject_product",
        "update_product_badge",
        "bulk_archive_products",
        "bulk_restore_products",
        "bulk_moderate_products",
        "bulk_change_category",
        "archive_product",
        "restore_product_route",
        "delete_product_permanent",
    ]

    def test_no_underscore_parameter_in_signatures(self, admin_products_service):
        for fn_name in self.FUNCTIONS_WITH_FORMER_UNUSED_UNDERSCORE:
            fn = getattr(admin_products_service, fn_name)
            sig = inspect.signature(fn)
            assert "_" not in sig.parameters, f"{fn_name} still has unused _ parameter"

    def test_signature_count_unchanged_for_bulk_functions(self, admin_products_service):
        bulk_fns = {
            "bulk_archive_products": 4,
            "bulk_restore_products": 4,
            "bulk_moderate_products": 4,
            "bulk_change_category": 4,
            "archive_product": 5,
            "restore_product_route": 4,
            "delete_product_permanent": 4,
        }
        for fn_name, expected_count in bulk_fns.items():
            fn = getattr(admin_products_service, fn_name)
            sig = inspect.signature(fn)
            assert len(sig.parameters) == expected_count, f"{fn_name} expected {expected_count} params, got {len(sig.parameters)}"

    def test_signature_count_unchanged_for_simple_functions(self, admin_products_service):
        simple_fns = {
            "approve_product": 3,
            "reject_product": 4,
            "update_product_badge": 5,
        }
        for fn_name, expected_count in simple_fns.items():
            fn = getattr(admin_products_service, fn_name)
            sig = inspect.signature(fn)
            assert len(sig.parameters) == expected_count, f"{fn_name} expected {expected_count} params, got {len(sig.parameters)}"

    def test_list_all_products_signature(self, admin_products_service):
        sig = inspect.signature(admin_products_service.list_all_products)
        assert len(sig.parameters) == 6, f"list_all_products expected 6 params, got {len(sig.parameters)}"
        assert "db" in sig.parameters
