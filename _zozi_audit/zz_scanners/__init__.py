"""Scanner package.

Each module registers its checks against ``zz_core.registry`` at import time.
Import failures are collected (not fatal) so a partially-implemented audit
still runs.
"""
from __future__ import annotations

from importlib import import_module

_MODULES = [
    "preflight",
    "s01_architecture",
    "s02_technology",
    "s03_logic",
    "s04_operations",
    "s05_wiring",
    "s06_database",
    "s07_providers",
    "s08_laws",
    "s09_environment",
    "s10_tests",
    "s11_frontend",
    "s12_features",
    "s13_security",
    "s14_performance",
    "s15_crosscut",
    "s16_design",
    "s17_interactions",
    "s18_feature_matrix",
    "s19_workflow",
    "s20_db_advisor",
    "s21_http_layer",
]

IMPORT_ERRORS: dict[str, str] = {}

for _name in _MODULES:
    try:
        import_module(f"{__name__}.{_name}")
    except Exception as _exc:  # pragma: no cover
        IMPORT_ERRORS[_name] = f"{type(_exc).__name__}: {_exc}"
