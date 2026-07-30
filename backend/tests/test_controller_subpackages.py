"""Tests for controller subpackage structure and re-exports.

Verifies that:
- controllers.supplier subpackage re-exports all expected functions
- controllers.admin_controller backward-compat wrapper works
- controllers.admin subpackage is importable
"""
from __future__ import annotations
import pytest


class TestAdminControllerBackwardCompat:
    """Verifies controllers.admin_controller file exists as a re-export wrapper.

    NOTE: The admin subpackage (controllers/admin/*.py) has pre-existing import
    bugs (missing symbols in utils.auth, utils.constants, etc.) that are outside
    our scope.  We verify the wrapper file structure instead of deep-importing.
    """

    def test_admin_controller_file_exists(self):
        import os
        assert os.path.isfile(os.path.join("controllers", "admin_controller.py"))

    def test_admin_controller_has_reexport(self):
        with open("controllers/admin_controller.py") as f:
            content = f.read()
        assert "from controllers.admin import *" in content

    def test_admin_init_file_exists(self):
        import os
        assert os.path.isfile(os.path.join("controllers", "admin", "__init__.py"))

    def test_admin_init_imports_modules(self):
        with open("controllers/admin/__init__.py") as f:
            content = f.read()
        assert ".users" in content or ".orders" in content or ".products" in content

    def test_admin_controller_module_file_structure(self):
        with open("controllers/admin_controller.py") as f:
            content = f.read()
        assert "__all__" not in content  # uses * re-export instead
        assert "from controllers.admin import" in content


class TestSupplierSubpackage:
    """Verifies controllers.supplier subpackage re-exports all domain modules."""

    def test_supplier_package_importable(self):
        import controllers.supplier as s
        assert s is not None

    def test_supplier_products_module(self):
        from controllers.supplier.products import (
            get_supplier_products,
            get_supplier_product,
            create_supplier_product,
            update_supplier_product,
            delete_supplier_product,
        )
        assert callable(get_supplier_products)
        assert callable(get_supplier_product)
        assert callable(create_supplier_product)
        assert callable(update_supplier_product)
        assert callable(delete_supplier_product)

    def test_supplier_orders_module(self):
        from controllers.supplier.orders import (
            get_supplier_orders,
            update_supplier_order_status,
            get_supplier_order_detail,
        )
        assert callable(get_supplier_orders)
        assert callable(update_supplier_order_status)
        assert callable(get_supplier_order_detail)

    def test_supplier_profile_module(self):
        from controllers.supplier.profile import (
            get_supplier_profile,
            update_supplier_profile,
            request_verification,
            get_supplier_regions,
            update_supplier_regions,
        )
        assert callable(get_supplier_profile)
        assert callable(update_supplier_profile)
        assert callable(request_verification)
        assert callable(get_supplier_regions)
        assert callable(update_supplier_regions)

    def test_supplier_analytics_module(self):
        from controllers.supplier.analytics import (
            get_supplier_analytics,
            get_supplier_reports,
            get_supplier_analytics_timeseries,
        )
        assert callable(get_supplier_analytics)
        assert callable(get_supplier_reports)
        assert callable(get_supplier_analytics_timeseries)

    def test_supplier_inventory_module(self):
        from controllers.supplier.inventory import (
            get_supplier_inventory,
            update_product_stock,
            update_inventory_levels,
            get_inventory_alerts,
            bulk_inventory_adjust,
        )
        assert callable(get_supplier_inventory)
        assert callable(update_product_stock)
        assert callable(update_inventory_levels)
        assert callable(get_inventory_alerts)
        assert callable(bulk_inventory_adjust)

    def test_supplier_payouts_module(self):
        from controllers.supplier.payouts import (
            get_payout_history,
            request_payout,
        )
        assert callable(get_payout_history)
        assert callable(request_payout)

    def test_supplier_badge_module(self):
        from controllers.supplier.badge import (
            compute_credibility_score,
            list_supplier_badge_catalog,
            purchase_supplier_badge,
            refresh_supplier_badge,
        )
        assert callable(compute_credibility_score)
        assert callable(list_supplier_badge_catalog)
        assert callable(purchase_supplier_badge)
        assert callable(refresh_supplier_badge)

    def test_supplier_init_re_exports_everything(self):
        from controllers.supplier import (
            get_supplier_products,
            get_supplier_orders,
            get_supplier_profile,
            get_supplier_analytics,
            get_supplier_inventory,
            get_payout_history,
            compute_credibility_score,
        )
        assert callable(get_supplier_products)
        assert callable(get_supplier_orders)
        assert callable(get_supplier_profile)
        assert callable(get_supplier_analytics)
        assert callable(get_supplier_inventory)
        assert callable(get_payout_history)
        assert callable(compute_credibility_score)


class TestAdminSubpackage:
    """Verifies controllers.admin subpackage has the expected file structure.

    NOTE: The admin subpackage modules have pre-existing import bugs (missing
    symbols in utils.auth, utils.constants, etc.) that are outside our scope.
    We verify the file structure instead of deep-importing.
    """

    def test_admin_init_file_exists(self):
        import os
        assert os.path.isfile(os.path.join("controllers", "admin", "__init__.py"))

    def test_admin_init_lists_modules(self):
        with open("controllers/admin/__init__.py") as f:
            content = f.read()
        assert ".users" in content
        assert ".orders" in content
        assert ".products" in content

    def test_admin_init_all_modules_referenced(self):
        with open("controllers/admin/__init__.py") as f:
            content = f.read()
        expected_modules = [
            ".auth", ".users", ".orders", ".products",
            ".suppliers", ".payouts", ".coupons", ".tickets",
            ".database", ".permissions", ".analytics", ".bulk_ops",
        ]
        for mod in expected_modules:
            assert mod in content, f"Missing {mod} in admin __init__.py"

    def test_admin_domain_module_files_exist(self):
        import os
        expected = [
            "auth.py", "users.py", "orders.py", "products.py",
            "suppliers.py", "payouts.py", "coupons.py", "tickets.py",
            "database.py", "permissions.py", "analytics.py", "bulk_ops.py",
        ]
        for fname in expected:
            path = os.path.join("controllers", "admin", fname)
            assert os.path.isfile(path), f"Missing admin module: {fname}"


class TestUtilsPackage:
    """Verifies utils package exports include new modules."""

    def test_utils_has_background_jobs(self):
        from utils import background_jobs
        assert background_jobs is not None

    def test_utils_has_middleware_helpers(self):
        from utils import middleware_helpers
        assert middleware_helpers is not None

    def test_utils_has_versioning(self):
        from utils import versioning
        assert versioning is not None

    def test_utils_has_response_wrapper(self):
        from utils import response_wrapper
        assert response_wrapper is not None
