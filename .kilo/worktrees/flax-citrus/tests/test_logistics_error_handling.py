"""
Regression tests for the Logistics feature error-handling hardening.

Guard rail: confirms that genuine swallowed-exception patterns
(`except ...: pass` immediately followed by a logger call, or a
misleading "Exception in unknown function" message) have NOT crept back
into the logistics feature modules that were cleaned up.
"""
from __future__ import annotations

import ast
import py_compile
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"

LOGISTICS_FILES = [
    BACKEND / "services" / "logistics" / "logistics_sla_service.py",
    BACKEND / "providers" / "logistics" / "geo.py",
    BACKEND / "controllers" / "logistics" / "logistics_partner_controller.py",
]

SWALLOWED_PATTERNS = [
    'pass\n            logger.exception("Handled Exception")',
    "pass\n            logger.exception('Exception in unknown function",
    "logger.exception('Exception in unknown function (handled gracefully)')",
]


def _assert_no_swallowed(source: str) -> None:
    for bad in SWALLOWED_PATTERNS:
        assert bad not in source, f"swallowed-exception pattern still present: {bad!r}"

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            body = node.body
            if (
                len(body) == 2
                and isinstance(body[0], ast.Pass)
                and isinstance(body[1], ast.Expr)
                and isinstance(body[1].value, ast.Call)
            ):
                raise AssertionError(
                    "except block with `pass` then a single call (swallowed exception) found"
                )


def test_logistics_files_compile() -> None:
    for f in LOGISTICS_FILES:
        assert f.exists(), f"missing {f}"
        py_compile.compile(str(f), doraise=True)


def test_no_swallowed_exceptions_in_logistics() -> None:
    for f in LOGISTICS_FILES:
        _assert_no_swallowed(f.read_text(encoding="utf-8"))


def test_improved_messages_present() -> None:
    sla = (BACKEND / "services" / "logistics" / "logistics_sla_service.py").read_text(
        encoding="utf-8"
    )
    assert "falling back to Mon-Sat" in sla

    geo = (BACKEND / "providers" / "logistics" / "geo.py").read_text(encoding="utf-8")
    assert "GeoIP2 country lookup failed" in geo

    ctrl = (
        BACKEND / "controllers" / "logistics" / "logistics_partner_controller.py"
    ).read_text(encoding="utf-8")
    assert "Invalid expires_at" in ctrl
