"""G-12 paired tests — regression suite for the five confirmed defects.

Each test guards a specific fix so the defect cannot silently reappear.

C1  : ``customer_service`` module must be importable from ``domains.customers.services``
C2  : ``domains.customers.services.core`` must exist and export ``CustomerService``
D1  : ``domains.catalog.services.search.search_service`` must not import models directly
D2  : ``Product`` must accept ``currency`` as a constructor kwarg
D3  : ``Product.cart_items`` relationship must resolve without ArgumentError
"""
from __future__ import annotations

import ast
import inspect
import textwrap


# ── C1: customer_service module must be importable ────────────────────────

class TestC1CustomerServiceModuleImportable:
    def test_import_customer_service_from_services(self):
        from domains.customers.services import customer_service
        assert customer_service is not None

    def test_customer_service_exports_customer_service_class(self):
        from domains.customers.services import customer_service
        assert hasattr(customer_service, "CustomerService")

    def test_customer_service_is_module_not_just_attribute(self):
        import domains.customers.services as svc_pkg
        assert hasattr(svc_pkg, "customer_service")


# ── C2: core sub-package must exist and export CustomerService ─────────────

class TestC2CoreSubPackageExists:
    def test_core_module_importable(self):
        import domains.customers.services.core  # noqa: F401
        assert hasattr(domains.customers.services.core, "CustomerService"), (
            "domains.customers.services.core must export CustomerService"
        )

    def test_customer_service_class_importable_from_core(self):
        from domains.customers.services.core.customer_service import CustomerService
        assert callable(CustomerService)

    def test_core_init_exists(self):
        import importlib
        mod = importlib.import_module("domains.customers.services.core")
        assert mod is not None


# ── D1: Law 3 — search/search_service.py must not import models directly ───

class TestD1NoDirectModelImportsInSearchService:
    def _get_search_service_source(self) -> str:
        import domains.catalog.services.search.search_service as ss_mod
        src_file = inspect.getsourcefile(ss_mod)
        with open(src_file, "r", encoding="utf-8") as fh:
            return fh.read()

    def test_no_direct_catalog_model_imports(self):
        src = self._get_search_service_source()
        tree = ast.parse(textwrap.dedent(src))
        forbidden: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("domains.catalog.models"):
                    forbidden.append(ast.dump(node))
        assert forbidden == [], (
            "search/search_service.py must not import directly from "
            "domains.catalog.models; use domains.catalog.ports instead. "
            f"Found: {forbidden}"
        )

    def test_imports_product_from_ports(self):
        """Product must be reachable via ports (Law 3)."""
        from domains.catalog.ports import Product
        assert Product is not None

    def test_search_service_exposes_smart_search(self):
        from domains.catalog.services.search.search_service import smart_search
        assert callable(smart_search)


# ── D2: Product must accept currency kwarg ────────────────────────────────

class TestD2ProductAcceptsCurrencyKwarg:
    def test_currency_column_exists_in_model(self):
        from domains.catalog.models.products import Product
        assert "currency" in [c.name for c in Product.__table__.columns]

    def test_product_constructor_accepts_currency_kwarg(self):
        from domains.catalog.models.products import Product
        # Should not raise TypeError when currency is passed
        inst = Product(name="Test", price=10, currency="USD")
        assert hasattr(inst, "currency")
        assert inst.currency == "USD"

    def test_default_currency_is_usd(self):
        from domains.catalog.models.products import Product
        col = Product.__table__.columns["currency"]
        assert col.default.arg == "USD"  # type: ignore[union-attr]


# ── D3: Product.cart_items relationship must resolve ──────────────────────

class TestD3CartItemsRelationshipResolves:
    def test_product_has_cart_items_relationship(self):
        from domains.catalog.models.products import Product
        assert "cart_items" in Product.__mapper__.relationships

    def test_cart_items_back_populates_product(self):
        from domains.catalog.models.products import Product
        rel = Product.__mapper__.relationships["cart_items"]
        assert rel.back_populates == "product"

    def test_product_reviews_back_populates_product(self):
        from domains.catalog.models.products import Product
        rel = Product.__mapper__.relationships["reviews"]
        assert rel.back_populates == "product"

    def test_product_wishlist_items_back_populates_product(self):
        from domains.catalog.models.products import Product
        rel = Product.__mapper__.relationships["wishlist_items"]
        assert rel.back_populates == "product"
