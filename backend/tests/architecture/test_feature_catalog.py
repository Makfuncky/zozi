"""Law 4 gate: features are single-sourced and aggregated by rbac/catalog.py.

Law 4:
  * Features are single-sourced in ``domains/*/features.py`` (each domain owns
    exactly one ``FEATURES`` map).
  * ``rbac/catalog.py`` aggregates every domain's ``FEATURES`` into the single
    catalog of record. A feature string must never be invented in a router;
    CI fails on any ``require_feature("...")`` literal not present in the catalog.

This gate verifies:
  1. Every domain package exposes ``domains/<domain>/features.py`` with a
     ``FEATURES`` dict.
  2. ``rbac.catalog`` loads and its catalog is the union of all domain features
     (single source of truth).
  3. Every ``require_feature("<literal>")`` string literal found in the module
     routers is present in the catalog.
"""
from __future__ import annotations

import ast
import glob
import importlib
import os

BACKEND = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DOMAINS_DIR = os.path.join(BACKEND, "domains")
MODULES_DIR = os.path.join(BACKEND, "modules")


def _domain_names():
    if not os.path.isdir(DOMAINS_DIR):
        return []
    return sorted(
        d for d in os.listdir(DOMAINS_DIR)
        if os.path.isdir(os.path.join(DOMAINS_DIR, d))
        and not d.startswith("_")
        and os.path.isfile(os.path.join(DOMAINS_DIR, d, "features.py"))
    )


def _load_catalog():
    import rbac.catalog as catalog
    catalog._load()
    return catalog


class TestFeaturesSingleSourced:
    def test_every_domain_exposes_features_module(self):
        # Find all domain packages (directories under domains/) and require each
        # to provide a single-sourced features.py.
        domains = [
            d for d in os.listdir(DOMAINS_DIR)
            if os.path.isdir(os.path.join(DOMAINS_DIR, d)) and not d.startswith("_")
        ]
        missing = [
            d for d in domains
            if not os.path.isfile(os.path.join(DOMAINS_DIR, d, "features.py"))
        ]
        assert not missing, (
            "Law 4: every domain must single-source its features in "
            "domains/<domain>/features.py. Missing:\n  " + "\n  ".join(missing)
        )

    def test_features_module_defines_features_dict(self):
        for name in _domain_names():
            mod = importlib.import_module(f"domains.{name}.features")
            assert hasattr(mod, "FEATURES"), (
                f"domains.{name}.features must define FEATURES (Law 4)"
            )
            assert isinstance(mod.FEATURES, dict), (
                f"domains.{name}.features.FEATURES must be a dict"
            )


class TestCatalogAggregation:
    def test_catalog_loads_and_is_nonempty(self):
        catalog = _load_catalog()
        assert isinstance(catalog.FEATURE_CATALOG, dict)
        assert catalog.FEATURE_CATALOG, (
            "rbac.catalog.FEATURE_CATALOG is empty — feature aggregation failed. "
            "Check rbac/catalog.py scanning of domains/*/features.py."
        )

    def test_catalog_is_single_source_of_truth(self):
        catalog = _load_catalog()
        errors = []
        for name in _domain_names():
            mod = importlib.import_module(f"domains.{name}.features")
            for key in mod.FEATURES:
                if not catalog.is_known(key):
                    errors.append(f"{key!r} (domain {name})")
        assert not errors, (
            "Law 4: these domain features are not present in rbac.catalog "
            "(the single source of truth):\n  " + "\n  ".join(errors)
        )

    def test_require_feature_literals_resolve_to_catalog(self):
        # Any require_feature("...") string literal in the module routers must
        # exist in the catalog. (None today is fine; this guards future drift.)
        catalog = _load_catalog()
        unknown = []
        if os.path.isdir(MODULES_DIR):
            for path in glob.glob(os.path.join(MODULES_DIR, "**", "*.py"), recursive=True):
                if os.path.basename(path) == "__init__.py":
                    continue
                try:
                    tree = ast.parse(open(path, encoding="utf-8").read())
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)):
                        continue
                    if node.func.id != "require_feature":
                        continue
                    if node.args and isinstance(node.args[0], ast.Constant) \
                            and isinstance(node.args[0].value, str):
                        lit = node.args[0].value
                        if '*' not in lit and not catalog.is_known(lit):
                            unknown.append(f"{os.path.relpath(path, BACKEND)}: require_feature({lit!r})")
        assert not unknown, (
            "Law 4: require_feature literal(s) not present in rbac.catalog:\n  "
            + "\n  ".join(unknown)
        )
