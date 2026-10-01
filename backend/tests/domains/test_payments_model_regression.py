"""Regression tests for FILE-29 findings in backend/domains/finance/models/payments.py.

Proves:
  - LAW-EXTRACT-002: payments.py does NOT directly import CountryConfig from
    domains.country.models.countries (cross-domain model import forbidden by Law 1).
  - DB-019: PaymentGatewayConnection.country_code declares a ForeignKey and an
    explicit index (Law 52, Law 53).
"""
from __future__ import annotations

import ast
import importlib
from pathlib import Path

import pytest


def _load_payments_module():
    """Import and return the payments models module."""
    return importlib.import_module("domains.finance.models.payments")


def _payments_source_text() -> str:
    """Return the raw source of payments.py as text."""
    mod = _load_payments_module()
    return Path(mod.__file__).read_text(encoding="utf-8")


class TestLawExtract002:
    """LAW-EXTRACT-002: no cross-domain CountryConfig import in payments.py."""

    def test_no_country_config_direct_import(self):
        """payments.py must not contain a direct import of CountryConfig."""
        text = _payments_source_text()
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "domains.country.models.countries":
                    names = [alias.name for alias in node.names]
                    assert "CountryConfig" not in names, (
                        "Direct import of CountryConfig from domains.country.models.countries "
                        "violates Law 1 (dependency direction)."
                    )

    def test_payment_country_relationship_uses_string_reference(self):
        """Payment.country relationship must use a string reference so SQLAlchemy
        resolves it lazily without a direct import at the top of the file."""
        text = _payments_source_text()
        tree = ast.parse(text)
        # Find the Payment class and its 'country' assignment
        found_string_ref = False
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "Payment":
                for item in node.body:
                    if (
                        isinstance(item, ast.Assign)
                        and any(t.id == "country" for t in item.targets if isinstance(t, ast.Name))
                    ):
                        # The relationship call should have a string first arg
                        call = item.value
                        if isinstance(call, ast.Call) and call.args:
                            first_arg = call.args[0]
                            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                                found_string_ref = True
        assert found_string_ref, (
            "Payment.country relationship does not appear to use a string reference "
            "for CountryConfig. A direct import may be present or the reference "
            "is not a string literal."
        )


class TestDB019:
    """DB-019: PaymentGatewayConnection.country_code must have FK and index."""

    def test_country_code_has_foreign_key(self):
        """PaymentGatewayConnection.country_code must declare a ForeignKey."""
        mod = _load_payments_module()
        col = mod.PaymentGatewayConnection.__table__.c.country_code
        assert len(col.foreign_keys) > 0, (
            "PaymentGatewayConnection.country_code has no ForeignKey."
        )
        fk = next(iter(col.foreign_keys))
        target = fk.column.table.fullname
        assert target == "country.country_configs", (
            f"Unexpected FK target: {target}. "
            'Expected country.country_configs.code'
        )

    def test_country_code_has_index(self):
        """PaymentGatewayConnection.country_code must have an explicit index."""
        mod = _load_payments_module()
        table = mod.PaymentGatewayConnection.__table__
        index_names = [idx.name for idx in table.indexes]
        country_indexes = [
            idx for idx in table.indexes if "country_code" in [c.name for c in idx.columns]
        ]
        assert len(country_indexes) > 0, (
            "PaymentGatewayConnection.country_code has no explicit index. "
            f"Indexes present: {index_names}"
        )

    def test_country_code_nullable_for_set_null(self):
        """country_code must be nullable when ondelete='SET NULL'."""
        mod = _load_payments_module()
        col = mod.PaymentGatewayConnection.__table__.c.country_code
        assert col.nullable is True, (
            "PaymentGatewayConnection.country_code is non-nullable but the FK "
            "uses ondelete='SET NULL', which requires nullable=True."
        )

    def test_country_code_pattern_matches_sibling_models(self):
        """PaymentGatewayConnection.country_code definition must match the pattern
        used by Payment, Payout, and LogisticsPartnerPayout in the same file."""
        mod = _load_payments_module()
        pgc_col = mod.PaymentGatewayConnection.__table__.c.country_code
        payment_col = mod.Payment.__table__.c.country_code
        # Both must have ForeignKeys and both must be indexed
        assert len(pgc_col.foreign_keys) > 0
        assert len(payment_col.foreign_keys) > 0
        pgc_indexed = any(
            "country_code" in [c.name for c in idx.columns] for idx in mod.PaymentGatewayConnection.__table__.indexes
        )
        payment_indexed = any(
            "country_code" in [c.name for c in idx.columns] for idx in mod.Payment.__table__.indexes
        )
        assert pgc_indexed and payment_indexed, (
            "PaymentGatewayConnection and Payment country_code index status mismatch."
        )
