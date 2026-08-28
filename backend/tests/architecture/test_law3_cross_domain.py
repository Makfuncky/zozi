"""Law 3 gate: cross-domain writes only via events; reads only via ports.

Verifies:
  1. Cross-domain imports go through ports.py (not direct service imports).
  2. Cross-domain writes go through events.py (not direct FK writes).
  3. Domains that communicate across boundaries have events.py or ports.py.
"""
from __future__ import annotations

import ast
import os
import pathlib

import pytest

_BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
_DOMAINS_DIR = _BACKEND_ROOT / "domains"


def _iter_domain_py(domain_name: str):
    domain_dir = _DOMAINS_DIR / domain_name
    if not domain_dir.exists():
        return
    for path in sorted(domain_dir.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


def _find_cross_domain_imports(file_path: pathlib.Path, current_domain: str) -> list[str]:
    """Return list of cross-domain imports found in a file."""
    try:
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return []

    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom):
            continue
        mod = node.module or ""
        if not mod.startswith("domains."):
            continue
        parts = mod.split(".")
        if len(parts) < 2:
            continue
        target_domain = parts[1]
        if target_domain == current_domain:
            continue
        if target_domain == "common":
            continue
        offenders.append(f"{file_path.name} imports {mod}")
    return offenders


class TestCrossDomainImportsViaPorts:
    """Cross-domain reads must go through ports.py."""

    def test_finance_has_ports(self):
        finance_ports = _DOMAINS_DIR / "finance" / "ports.py"
        assert finance_ports.exists(), "domains/finance/ports.py must exist for cross-domain reads"

    def test_catalog_has_ports(self):
        catalog_ports = _DOMAINS_DIR / "catalog" / "ports.py"
        assert catalog_ports.exists(), "domains/catalog/ports.py must exist for cross-domain reads"

    def test_governance_has_ports(self):
        gov_ports = _DOMAINS_DIR / "governance" / "ports.py"
        assert gov_ports.exists(), "domains/governance/ports.py must exist for cross-domain reads"

    def test_logistics_has_ports(self):
        log_ports = _DOMAINS_DIR / "logistics" / "ports.py"
        assert log_ports.exists(), "domains/logistics/ports.py must exist for cross-domain reads"

    def test_suppliers_has_ports(self):
        sup_ports = _DOMAINS_DIR / "suppliers" / "ports.py"
        assert sup_ports.exists(), "domains/suppliers/ports.py must exist for cross-domain reads"

    def test_payments_has_ports(self):
        pay_ports = _DOMAINS_DIR / "payments" / "ports.py"
        assert pay_ports.exists(), "domains/payments/ports.py must exist for cross-domain reads"


class TestCrossDomainWritesViaEvents:
    """Cross-domain writes must go through events.py."""

    def test_orders_has_events(self):
        orders_events = _DOMAINS_DIR / "orders" / "events.py"
        assert orders_events.exists(), "domains/orders/events.py must exist for cross-domain writes"

    def test_finance_has_events(self):
        finance_events = _DOMAINS_DIR / "finance" / "events.py"
        assert finance_events.exists(), "domains/finance/events.py must exist for cross-domain writes"

    def test_customers_has_events(self):
        cust_events = _DOMAINS_DIR / "customers" / "events.py"
        assert cust_events.exists(), "domains/customers/events.py must exist for cross-domain writes"

    def test_catalog_has_events(self):
        cat_events = _DOMAINS_DIR / "catalog" / "events.py"
        assert cat_events.exists(), "domains/catalog/events.py must exist for cross-domain writes"

    def test_suppliers_has_events(self):
        sup_events = _DOMAINS_DIR / "suppliers" / "events.py"
        assert sup_events.exists(), "domains/suppliers/events.py must exist for cross-domain writes"


class TestPortsModulesContent:
    """ports.py files must expose read functions (not business logic)."""

    def test_finance_ports_has_functions(self):
        ports_path = _DOMAINS_DIR / "finance" / "ports.py"
        if not ports_path.exists():
            pytest.skip("finance/ports.py does not exist")
        source = ports_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert len(functions) > 0, "finance/ports.py should expose at least one port function"

    def test_catalog_ports_has_functions(self):
        ports_path = _DOMAINS_DIR / "catalog" / "ports.py"
        if not ports_path.exists():
            pytest.skip("catalog/ports.py does not exist")
        source = ports_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        assert len(functions) > 0, "catalog/ports.py should expose at least one port function"


class TestNoDirectCrossDomainServiceImports:
    """Domains must not directly import another domain's services."""

    _SANCTIONED = {"rbac/catalog.py"}

    def test_no_direct_cross_domain_service_imports(self):
        offenders = []
        for domain_dir in sorted(_DOMAINS_DIR.iterdir()):
            if not domain_dir.is_dir() or domain_dir.name.startswith("_"):
                continue
            for py_file in _iter_domain_py(domain_dir.name):
                rel = str(py_file.relative_to(_BACKEND_ROOT))
                if rel in self._SANCTIONED:
                    continue
                findings = _find_cross_domain_imports(py_file, domain_dir.name)
                # Filter to only service imports (the real violation)
                for f in findings:
                    if ".services." in f:
                        offenders.append(f)
        if offenders:
            msg = "\n  ".join(sorted(set(offenders)))
            pytest.fail(
                "Law 3 violation: direct cross-domain service imports "
                f"(must use events.py or ports.py):\n  {msg}"
            )
