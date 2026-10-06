"""Durable regression guard for the orders/ports.py cross-domain surface.

Two-tier strategy:

1. **Static guard** — scans the source tree for ``from domains.orders.ports
   import X`` and verifies that every ``X`` is either defined directly in
   ``ports.py`` or registered in ``_LAZY_SERVICE_EXPORTS``. This catches
   silent port-surface removals at *collection* time without importing heavy
   application modules.

2. **Runtime guard** — imports a small, known-good subset of the port surface
   (symbols whose underlying modules do not require a database connection at
   import time) and asserts they are callable. This catches cases where the
   static guard passes but the lazy-export target module has been deleted or
   renamed.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
_DOMAINS_ROOT = _BACKEND_ROOT / "domains"
_ORDERS_PORTS = _BACKEND_ROOT / "domains" / "orders" / "ports.py"


def _iter_domain_dirs() -> list[pathlib.Path]:
    """Return every sub-directory of ``domains/`` except ``orders`` itself."""
    return [
        p for p in _DOMAINS_ROOT.iterdir()
        if p.is_dir() and p.name != "orders"
    ]


def _collect_imported_symbols() -> set[str]:
    """Scan every non-orders domain for ``from domains.orders.ports import X``."""
    symbols: set[str] = set()
    for domain_dir in _iter_domain_dirs():
        for py_file in domain_dir.rglob("*.py"):
            try:
                source = py_file.read_text(encoding="utf-8")
            except OSError:
                continue
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module == "domains.orders.ports":
                        for alias in node.names:
                            symbols.add(alias.name)
    return symbols


class TestOrdersPortsResolverGuard:
    """Every cross-domain symbol imported from orders/ports.py must resolve."""

    def test_static_port_surface_covers_all_cross_domain_imports(self):
        """Every consumer import is registered on the ports surface."""
        imported = _collect_imported_symbols()
        assert imported, "No cross-domain imports from domains.orders.ports found?"

        source = _ORDERS_PORTS.read_text(encoding="utf-8")
        tree = ast.parse(source)

        direct_names: set[str] = set()
        lazy_names: set[str] = set()
        defined_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == "domains.orders.services.tracking.service":
                    for alias in node.names:
                        direct_names.add(alias.name)
                if node.module == "domains.orders.models.orders":
                    for alias in node.names:
                        direct_names.add(alias.name)
            if isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = []
                if isinstance(node, ast.Assign):
                    targets = node.targets
                elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                    targets = [node.target]
                for target in targets:
                    if isinstance(target, ast.Name) and target.id == "_LAZY_SERVICE_EXPORTS":
                        if isinstance(node.value, ast.Dict):
                            for key in node.value.keys:
                                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                                    lazy_names.add(key.value)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defined_names.add(node.name)

        surface_names = direct_names | lazy_names | defined_names
        missing_from_lazy = imported - surface_names

        assert not missing_from_lazy, (
            "The following symbols are imported from domains.orders.ports "
            "but are missing from both the direct imports and "
            "_LAZY_SERVICE_EXPORTS:\n" + "\n".join(sorted(missing_from_lazy))
        )

    def test_shipment_scan_codes_resolves(self):
        """Specific regression guard for the prior silent-removal defect."""
        from domains.orders.ports import shipment_scan_codes

        assert callable(shipment_scan_codes)

    def test_shipment_event_label_resolves(self):
        """Guard for the tracking-service sibling that was also missing."""
        from domains.orders.ports import shipment_event_label

        assert callable(shipment_event_label)
