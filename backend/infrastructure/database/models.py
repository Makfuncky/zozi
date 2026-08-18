"""ORM model registry facade.

The old ``_legacy.models`` aggregator re-exported every ORM class so that layers
which must not depend on a top-level ``models`` package (utils, middleware,
dependencies) could still reach model classes through ``db.models``. That
aggregator is gone; this module now performs the same job by walking every
``domains.<d>.models`` package and re-exporting its classes unchanged.
"""
from __future__ import annotations

import importlib
import pkgutil
import types as _types

import domains

_g = globals()
_seen: set[str] = set()


def _collect(pkg: str) -> None:
    try:
        _m = importlib.import_module(pkg)
    except Exception:
        return
    if hasattr(_m, "__path__"):
        for _e in pkgutil.iter_modules(_m.__path__):
            _collect(f"{pkg}.{_e.name}")
    for _n in dir(_m):
        if _n.startswith("_"):
            continue
        _v = getattr(_m, _n)
        if isinstance(_v, _types.ModuleType):
            continue
        if _n in _seen:
            continue
        _seen.add(_n)
        _g[_n] = _v


for _entry in pkgutil.iter_modules(domains.__path__):
    _collect(f"domains.{_entry.name}.models")
