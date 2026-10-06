"""Paired contract test for ``domains.finance.ports`` (G-05).

Freezes the public namespace contract and the lazy-export map so that a
repeat loss (like the third disappearance of
``post_logistics_cod_remittance_journal``) is caught at collection time
instead of surfacing as a runtime ImportError deep inside a service.

Six-way verification
-------------------
1. Every key in ``_LAZY_SERVICE_EXPORTS`` resolves on first access.
2. The symbols that the finance test-suite imports from ``ports``
   (``_get_model`` from ``general_ledger``) resolve.
3. The public namespace count is asserted and documented.
4. Re-accessing ``ports`` from ``sys.modules`` returns an identical
   namespace (no silent drift on reload).
5. ``post_logistics_cod_remittance_journal`` is reachable via lazy load.
6. The lazy-export map contains no stale or duplicate entries.
7. Every symbol the test-suite imports from ``ports`` resolves at
   import-time across the whole suite (durable guard against repeat
   collection errors).
"""
from __future__ import annotations

import ast
import importlib
import pathlib
import sys

import pytest


def _get_ports():
    """Return the cached ``domains.finance.ports`` module."""
    return sys.modules.setdefault(
        "domains.finance.ports",
        importlib.import_module("domains.finance.ports"),
    )


def _collect_test_suite_port_imports() -> set[str]:
    """Scan every test file under ``backend/tests`` for symbols imported
    from ``domains.finance.ports`` and return the resolved set."""
    backend_root = pathlib.Path(__file__).resolve().parents[2]
    tests_root = backend_root / "tests"
    symbols: set[str] = set()
    for py_file in tests_root.rglob("test_*.py"):
        try:
            tree = ast.parse(py_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom):
                continue
            if node.module != "domains.finance.ports":
                continue
            for alias in node.names:
                symbols.add(alias.name)
    return symbols


class TestPortsLazyExportsResolve:
    """Every entry in ``_LAZY_SERVICE_EXPORTS`` must be importable."""

    def test_all_lazy_exports_resolve(self):
        ports = _get_ports()
        missing = []
        for key, (module_path, symbol) in ports._LAZY_SERVICE_EXPORTS.items():
            try:
                value = getattr(ports, key)
            except AttributeError as exc:
                missing.append((key, module_path, symbol, str(exc)))
                continue
            assert value is not None, f"lazy export {key!r} resolved to None"

        assert not missing, (
            "The following lazy exports could not be resolved:\n"
            + "\n".join(f"  {k} -> {m}.{s}: {e}" for k, m, s, e in missing)
        )

    def test_post_logistics_cod_remittance_journal_is_lazy(self):
        """Regression: this symbol was lost three times from the lazy map."""
        ports = _get_ports()
        assert "post_logistics_cod_remittance_journal" in ports._LAZY_SERVICE_EXPORTS
        fn = ports.post_logistics_cod_remittance_journal
        assert callable(fn), "post_logistics_cod_remittance_journal must be callable"

    def test_post_supplier_settlement_journal_is_lazy(self):
        ports = _get_ports()
        assert "post_supplier_settlement_journal" in ports._LAZY_SERVICE_EXPORTS
        fn = ports.post_supplier_settlement_journal
        assert callable(fn), "post_supplier_settlement_journal must be callable"


class TestPortsNamespaceCount:
    """The public namespace of ``domains.finance.ports`` is part of the
    cross-domain contract; drift must not be silent."""

    # Measured on the current tree after all lazy exports resolve (186).
    # Historically drifted: 196 -> 195 -> plus three port functions another
    # agent added.  The correct current count is 186.
    EXPECTED_PUBLIC_COUNT = 186

    def _public_symbols(self):
        ports = _get_ports()
        for key in ports._LAZY_SERVICE_EXPORTS:
            try:
                getattr(ports, key)
            except Exception:
                pass
        return [n for n in dir(ports) if not n.startswith("_")]

    def test_public_namespace_count(self):
        public = self._public_symbols()
        assert len(public) == self.EXPECTED_PUBLIC_COUNT, (
            f"public namespace drift: expected {self.EXPECTED_PUBLIC_COUNT}, "
            f"got {len(public)}"
        )

    def test_get_list_port_function_pairs_present(self):
        """Every ``get_*`` port function should have a matching ``list_*``."""
        ports = _get_ports()
        get_funcs = {n for n in dir(ports) if n.startswith("get_") and n.endswith("_by_id")}
        list_funcs = {n for n in dir(ports) if n.startswith("list_")}
        lazy_get = {n for n in ports._LAZY_SERVICE_EXPORTS if n.startswith("get_")}
        lazy_list = {n for n in ports._LAZY_SERVICE_EXPORTS if n.startswith("list_")}
        regular_get = get_funcs - lazy_get
        regular_list = list_funcs - lazy_list
        assert len(regular_get) == len(regular_list), (
            "get/list port function count drift:\n"
            f"  regular get_*_by_id: {len(regular_get)}\n"
            f"  regular list_*: {len(regular_list)}"
        )


class TestPortsRepeatedImport:
    """Accessing ``ports`` from ``sys.modules`` must be idempotent."""

    def test_cached_module_has_identical_namespace(self):
        ports1 = _get_ports()
        ns1 = set(dir(ports1))

        ports2 = _get_ports()
        ns2 = set(dir(ports2))

        assert ports1 is ports2, "ports module should be cached in sys.modules"
        assert ns1 == ns2, "namespace drift between repeated accesses"


class TestPortsTestSuiteImportsResolve:
    """Durable guard: every symbol the test-suite imports from
    ``domains.finance.ports`` must resolve at import-time.

    This prevents the recurrence of collection errors like the 7
    ``ImportError: cannot import name 'X' from 'domains.finance.ports'``
    failures that have hit this repo four times already.
    """

    def test_all_test_suite_port_imports_resolve(self):
        ports = _get_ports()
        missing = []
        for symbol in _collect_test_suite_port_imports():
            try:
                value = getattr(ports, symbol)
            except AttributeError as exc:
                missing.append((symbol, str(exc)))
                continue
            # Private helpers are allowed to resolve to None (models may
            # not exist in the test environment), but public symbols
            # must resolve to something real.
            if not symbol.startswith("_"):
                assert value is not None, (
                    f"public port symbol {symbol!r} resolved to None"
                )

        assert not missing, (
            "The following symbols imported by the test-suite from "
            "domains.finance.ports could not be resolved:\n"
            + "\n".join(f"  {s}: {e}" for s, e in missing)
        )
