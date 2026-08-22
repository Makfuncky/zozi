"""rbac/catalog.py - the feature registry (spec: AXIS 3 single source of truth).

Aggregates every domain's FEATURES dict via package scan so a feature string can
never be invented in a router. CI fails on any require_feature(...) literal not
present here.
"""
import importlib
import pkgutil

import domains

FEATURE_CATALOG: dict = {}

# Sanctioned namespace-wildcard prefixes (B4/R5 change-control). A module router may
# only gate on ``require_feature("X.*")`` if ``X`` is declared here, AND the
# namespace has backing atoms (Law 4) — checked by
# ``tests/architecture/test_require_feature_namespace_allowlist.py``.
#
# The codebase currently uses NO namespace-wildcard gates (all were expanded to
# explicit atoms), so this is empty. Adding a new ``require_feature("foo.*")``
# requires declaring ``foo`` here FIRST (CI fails otherwise), preventing silent
# RBAC drift. This set may only be edited deliberately; the gate keeps the
# codebase's actual wildcard usage in sync with this declaration (no unsanctioned
# gates, no dead declarations).
FEATURE_NAMESPACES: frozenset = frozenset()

def _load() -> None:
    for m in pkgutil.iter_modules(domains.__path__):
        try:
            feat = importlib.import_module(f"domains.{m.name}.features")
        except Exception:
            continue
        FEATURE_CATALOG.update(getattr(feat, "FEATURES", {}))

_load()

def is_known(feature: str) -> bool:
    return feature in FEATURE_CATALOG

def all_features() -> list:
    return list(FEATURE_CATALOG.keys())
