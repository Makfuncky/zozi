"""Catalog domain — architecture law tests (Laws 1, 3, 4, 6, 19, 22, 23, 55).

Verifies:
  * Schema discipline: every model declares a non-forbidden Postgres schema (Law 6/55).
  * Audit columns: created_at, updated_at, country_code, is_deleted (Law 23).
  * Foreign keys declare explicit ondelete (Law 22/52).
  * Features are single-sourced and present in the rbac catalog (Law 4).
  * events.py / ports.py are present and wired (Law 3).
  * Money uses Decimal/Numeric, never float (Law 19).
  * No forbidden cross-domain imports (Law 1).
"""
from __future__ import annotations

import ast
import pathlib

import pytest

from tests._support.laws import (
    assert_feature_in_catalog,
    assert_foreign_keys_have_ondelete,
    assert_no_forbidden_imports,
    assert_schema_discipline,
    iter_domain_models,
    load_feature_catalog,
)

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_CATALOG_ROOT = _BACKEND_ROOT / "domains" / "catalog"


# ---------------------------------------------------------------------------
# Law 6 / 55 — schema discipline
# ---------------------------------------------------------------------------


class TestCatalogSchemaDiscipline:
    """Every catalog ORM model must declare a valid Postgres schema."""

    def test_all_models_have_valid_schema(self, db_session):
        """All catalog models declare a non-forbidden schema (Law 6/55)."""
        failures: list[str] = []
        for model in iter_domain_models("catalog"):
            try:
                assert_schema_discipline(model)
            except AssertionError as exc:
                failures.append(str(exc))
        assert not failures, "Schema discipline failures:\n" + "\n".join(failures)

    def test_all_models_have_audit_columns(self, db_session):
        """All catalog models carry the required audit columns (Law 23)."""
        required = ("created_at", "updated_at", "country_code", "is_deleted")
        failures: list[str] = []
        for model in iter_domain_models("catalog"):
            missing = [c for c in required if not hasattr(model, c)]
            if missing:
                failures.append(f"{model.__name__}: missing {missing}")
        assert not failures, "Audit column failures:\n" + "\n".join(failures)

    def test_all_foreign_keys_have_ondelete(self, db_session):
        """Every ForeignKey on a catalog model declares explicit ondelete (Law 22/52)."""
        failures: list[str] = []
        for model in iter_domain_models("catalog"):
            try:
                assert_foreign_keys_have_ondelete(model)
            except AssertionError as exc:
                failures.append(str(exc))
        assert not failures, "FK ondelete failures:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# Law 19 — money uses Decimal / Numeric, never float
# ---------------------------------------------------------------------------


class TestCatalogMoneyTypes:
    """Money columns must use Numeric/Decimal, never float (Law 19)."""

    def test_no_float_columns_in_models(self, db_session):
        """No catalog model defines a Float column for money (Law 19)."""
        from sqlalchemy import Float

        offenders: list[str] = []
        for model in iter_domain_models("catalog"):
            for col in model.__table__.columns:
                if isinstance(col.type, Float):
                    offenders.append(f"{model.__name__}.{col.name}")
        assert not offenders, f"Float columns found (Law 19): {offenders}"

    def test_money_columns_are_numeric(self, db_session):
        """Price / cost / discount columns use Numeric (Law 19)."""
        from sqlalchemy import Numeric

        money_keywords = ("price", "cost", "discount", "amount", "commission_rate", "rating")
        for model in iter_domain_models("catalog"):
            for col in model.__table__.columns:
                if any(kw in col.name for kw in money_keywords):
                    assert isinstance(col.type, Numeric), (
                        f"{model.__name__}.{col.name} uses {type(col.type).__name__}, "
                        f"expected Numeric (Law 19)"
                    )


# ---------------------------------------------------------------------------
# Law 4 — features single-sourced in rbac catalog
# ---------------------------------------------------------------------------


class TestCatalogFeatures:
    """Catalog feature atoms must be registered in the rbac catalog."""

    def test_features_in_catalog(self):
        """Every catalog feature atom resolves in the aggregated catalog (Law 4)."""
        catalog = load_feature_catalog()
        from domains.catalog.features import FEATURES

        for key in FEATURES:
            assert key in catalog, f"Feature '{key}' missing from rbac catalog (Law 4)"

    def test_feature_values_are_descriptive(self):
        """Feature atoms must have non-empty descriptions (Law 4)."""
        from domains.catalog.features import FEATURES

        for key, desc in FEATURES.items():
            assert desc and isinstance(desc, str) and len(desc) > 5, (
                f"Feature '{key}' has inadequate description (Law 4)"
            )


# ---------------------------------------------------------------------------
# Law 3 — events.py / ports.py present & wired
# ---------------------------------------------------------------------------


class TestCatalogWiring:
    """events.py and ports.py must exist and expose the sanctioned surface."""

    def test_events_module_exists(self):
        """catalog domain has an events.py module (Law 3)."""
        assert (_CATALOG_ROOT / "events.py").exists(), "Missing events.py (Law 3)"

    def test_ports_module_exists(self):
        """catalog domain has a ports.py module (Law 3)."""
        assert (_CATALOG_ROOT / "ports.py").exists(), "Missing ports.py (Law 3)"

    def test_ports_expose_read_helpers(self, db_session):
        """ports.py exposes sanctioned read helpers (Law 3)."""
        from domains.catalog.ports import get_product_by_id, list_products, get_category_by_id

        assert callable(get_product_by_id)
        assert callable(list_products)
        assert callable(get_category_by_id)

    def test_ports_use_keyset_pagination(self, db_session):
        """ports.py list helpers use keyset pagination, never OFFSET (Law 222)."""
        source = (_CATALOG_ROOT / "ports.py").read_text(encoding="utf-8")
        assert "keyset_paginate" in source or "cursor_paginate" in source, (
            "ports.py must use keyset/cursor pagination (Law 222)"
        )


# ---------------------------------------------------------------------------
# Law 1 — no forbidden cross-domain imports
# ---------------------------------------------------------------------------


class TestCatalogImportHygiene:
    """catalog domain must not import forbidden layers (Law 1)."""

    def test_no_forbidden_imports(self):
        """catalog never imports modules, rbac, or other forbidden layers (Law 1)."""
        assert_no_forbidden_imports("domains", _CATALOG_ROOT)
