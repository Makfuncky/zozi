"""Regression tests for accounts/ports.py wiring correctness."""
from __future__ import annotations

import ast
import importlib
import inspect
import pathlib
import sys

import pytest


_BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[2]


def _get_ports():
    return sys.modules.setdefault(
        "domains.accounts.ports",
        importlib.import_module("domains.accounts.ports"),
    )


def _collect_imported_symbols() -> set[str]:
    symbols: set[str] = set()
    scan_roots = [_BACKEND_ROOT / "tests", _BACKEND_ROOT / "domains"]
    for scan_root in scan_roots:
        if not scan_root.exists():
            continue
        for py_file in scan_root.rglob("*.py"):
            if "_audit" in str(py_file):
                continue
            try:
                source = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "domains.accounts.ports":
                    for alias in node.names:
                        symbols.add(alias.name)
    return symbols


class TestOCRResultRelocation:
    """CONTR-013: OCRResult is colocated in accounts but belongs in media."""

    def test_ocr_result_import_surfaces_in_ports(self):
        """OCRResult import and helpers are present with relocation notice."""
        import domains.accounts.ports as ports

        assert hasattr(ports, "OCRResult")
        assert hasattr(ports, "get_o_c_r_result_by_id")
        assert hasattr(ports, "list_o_c_r_results")
        assert hasattr(ports, "list_o_c_r_results_page")

    def test_ocr_result_documented_as_colocated(self):
        """ports.py documents that OCRResult is colocated, not owned."""
        import domains.accounts.ports as ports

        source = inspect.getsource(ports)
        assert "media" in source.lower()
        assert "CONTR-013" in source


class TestAccountsPortsTestSuiteImportsResolve:
    """Durable guard: every symbol imported from ``domains.accounts.ports``
    anywhere under ``backend/tests`` and ``backend/domains`` must resolve at
    import-time.

    This prevents the recurrence of ``AttributeError: module 'domains.accounts.ports'
    has no attribute 'X'`` collection/runtime failures.
    """

    def test_all_imported_symbols_resolve(self):
        ports = _get_ports()
        missing = []
        for symbol in _collect_imported_symbols():
            try:
                value = getattr(ports, symbol)
            except AttributeError as exc:
                missing.append((symbol, str(exc)))
                continue
            if not symbol.startswith("_"):
                assert value is not None, (
                    f"public port symbol {symbol!r} resolved to None"
                )

        assert not missing, (
            "The following symbols imported from domains.accounts.ports "
            "could not be resolved:\n"
            + "\n".join(f"  {s}: {e}" for s, e in missing)
        )

    def test_lazy_export_map_has_no_stale_entries(self):
        ports = _get_ports()
        missing = []
        for key, (module_path, symbol) in ports._LAZY_SERVICE_EXPORTS.items():
            try:
                getattr(ports, key)
            except AttributeError as exc:
                missing.append((key, module_path, symbol, str(exc)))

        assert not missing, (
            "The following lazy exports could not be resolved:\n"
            + "\n".join(f"  {k} -> {m}.{s}: {e}" for k, m, s, e in missing)
        )
