"""rbac/catalog.py - the feature registry (spec: AXIS 3 single source of truth).

Aggregates every domain's FEATURES dict via package scan so a feature string can
never be invented in a router. CI fails on any require_feature(...) literal not
present here.
"""
import importlib
import pkgutil

import domains

FEATURE_CATALOG: dict = {}

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
