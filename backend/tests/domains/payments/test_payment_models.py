"""Paired test for F-03: payment_models duplicate-table cascade fix.

Verifies:
  1. configure_mappers() succeeds after the PaymentIntent __table_args__ fix.
  2. payments.payment_methods appears exactly once in Base.metadata.
  3. The module imports cleanly on repeated import (no duplicate-table error).
"""
from __future__ import annotations

import importlib
import sys

import pytest


def _clear_payments_modules():
    """Remove all payments domain modules from sys.modules."""
    for key in list(sys.modules.keys()):
        if "domains.payments" in key:
            del sys.modules[key]


def test_double_import_does_not_raise() -> None:
    """Re-importing the payment_models module must not raise InvalidRequestError.

    The original bug: PaymentIntent.__table_args__ had {'schema': 'payments'}
    as the *first* tuple element instead of the last. SQLAlchemy processed it
    as a constraint object, raising ArgumentError and aborting module
    registration. A later re-import then re-executed the module body and
    registered PaymentMethod a second time, producing:

        InvalidRequestError: Table 'payments.payment_methods' is already defined

    After moving the schema dict to the last position, the module should load
    cleanly on every import.
    """
    import subprocess

    # Run the import in a subprocess to get a completely fresh Python
    # interpreter (fresh sys.modules, fresh Base.metadata). This is the
    # only reliable way to verify the "double-import" scenario described
    # in the bug report.
    script = """
import sys
sys.path.insert(0, r"__BACKEND_ROOT__")
import domains.payments.models.payment_models as mod1
print("first_import_ok")
import domains.payments.models as mod2
print("second_import_ok")
from infrastructure.database.base import Base
tables = [t.name for t in Base.metadata.tables.values() if t.name == "payment_methods"]
assert len(tables) == 1, f"Expected 1 payment_methods, got {len(tables)}"
print("count_ok")
"""
    backend_root = str(
        __import__("pathlib").Path(__file__).resolve().parents[3]
    )
    script = script.replace("__BACKEND_ROOT__", backend_root)

    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Subprocess import failed (returncode={result.returncode})\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "first_import_ok" in result.stdout
    assert "second_import_ok" in result.stdout
    assert "count_ok" in result.stdout


def test_configure_mappers_succeeds() -> None:
    """configure_mappers() must not raise for the payments domain models."""
    from sqlalchemy.orm import configure_mappers

    configure_mappers()


def test_payment_methods_appears_once_in_metadata() -> None:
    """payments.payment_methods must be registered exactly once."""
    from infrastructure.database.base import Base

    payment_methods_tables = [
        t for t in Base.metadata.tables.values() if t.name == "payment_methods"
    ]
    assert len(payment_methods_tables) == 1, (
        f"Expected exactly one payment_methods table in metadata, "
        f"found {len(payment_methods_tables)}: {payment_methods_tables}"
    )
    assert payment_methods_tables[0].schema == "payments", (
        f"payment_methods schema should be 'payments', "
        f"got '{payment_methods_tables[0].schema}'"
    )


def test_payment_intent_table_args_schema_dict_is_last() -> None:
    """PaymentIntent.__table_args__ must have {'schema': ...} as the last element."""
    import ast
    from pathlib import Path

    mod_path = (
        Path(__file__).resolve().parents[3]
        / "domains"
        / "payments"
        / "models"
        / "payment_models.py"
    )
    source = mod_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for cls in ast.walk(tree):
        if not isinstance(cls, ast.ClassDef):
            continue
        if cls.name != "PaymentIntent":
            continue
        for node in cls.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(
                isinstance(t, ast.Name) and t.id == "__table_args__" for t in node.targets
            ):
                continue
            elems = getattr(node.value, "elts", [])
            dict_indices = [i for i, e in enumerate(elems) if isinstance(e, ast.Dict)]
            assert dict_indices, "PaymentIntent.__table_args__ has no schema dict"
            assert dict_indices[-1] == len(elems) - 1, (
                "PaymentIntent.__table_args__ schema dict is not the last element"
            )
            return

    pytest.fail("PaymentIntent.__table_args__ not found in payment_models.py")
