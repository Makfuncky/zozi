"""Law 4/161 — feature single-source guard.

Verifies:
  1. Every domain's ``features.py`` has a non-empty ``FEATURES`` dict.
  2. Every ``require_feature("<literal>")`` string literal found in ``modules/``
     resolves to the aggregated rbac catalog.
  3. Every ``require_module("<literal>")`` string literal found in ``modules/``
     resolves to a known module name.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests._support import laws

_BACKEND = laws.BACKEND_ROOT
_MODULES_DIR = _BACKEND / "modules"


def _iter_py(root: Path):
    if not root.exists():
        return
    for path in sorted(root.rglob("*.py")):
        if path.name == "__init__.py":
            continue
        yield path


class TestEveryDomainFeaturesNonEmpty:
    """Law 4/157: every domain's FEATURES dict must be non-empty."""

    @pytest.mark.parametrize("domain", laws.ALL_DOMAINS)
    def test_features_dict_nonempty(self, domain):
        mod_path = _BACKEND / "domains" / domain / "features.py"
        assert mod_path.exists(), (
            f"Law 4: domain {domain} missing features.py"
        )
        try:
            mod = laws.import_module(f"domains.{domain}.features")
        except ImportError as exc:
            pytest.fail(f"Cannot import domains.{domain}.features: {exc}")

        assert hasattr(mod, "FEATURES"), f"domains.{domain}.features missing FEATURES"
        assert isinstance(mod.FEATURES, dict), f"domains.{domain}.features.FEATURES not a dict"
        assert mod.FEATURES, f"domains.{domain}.features.FEATURES is empty (Law 4)"


class TestRequireFeatureLiteralsResolve:
    """Law 4/161: every require_feature("...") literal in modules/ must be in catalog."""

    def test_require_feature_literals_in_catalog(self):
        catalog = laws.load_feature_catalog()
        if not catalog:
            pytest.skip("Feature catalog is empty — cannot validate literals")

        unknown: list[str] = []
        if not _MODULES_DIR.exists():
            pytest.skip("modules/ directory does not exist")

        for path in _iter_py(_MODULES_DIR):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name != "require_feature":
                    continue
                if not node.args:
                    continue
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    lit = arg.value
                    if "*" in lit:
                        continue  # wildcard patterns are namespace-level
                    if lit not in catalog:
                        unknown.append(f"{path.relative_to(_BACKEND)}: require_feature({lit!r})")

        assert not unknown, (
            "Law 4/161 violation: require_feature literal(s) not in catalog:\n  "
            + "\n  ".join(sorted(set(unknown)))
        )


class TestRequireModuleLiteralsResolve:
    """Law 138: every require_module("...") literal must be a known module."""

    def test_require_module_literals_are_known(self):
        if not _MODULES_DIR.exists():
            pytest.skip("modules/ directory does not exist")

        unknown: list[str] = []
        for path in _iter_py(_MODULES_DIR):
            try:
                source = path.read_text(encoding="utf-8")
                tree = ast.parse(source)
            except (OSError, SyntaxError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name != "require_module":
                    continue
                if not node.args:
                    continue
                arg = node.args[0]
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    lit = arg.value
                    if lit not in laws.ALL_MODULES:
                        unknown.append(f"{path.relative_to(_BACKEND)}: require_module({lit!r})")

        assert not unknown, (
            "Law 138 violation: require_module literal(s) not a known module:\n  "
            + "\n  ".join(sorted(set(unknown)))
        )
