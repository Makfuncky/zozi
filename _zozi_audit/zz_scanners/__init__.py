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
    # s22 was written but never added here, so none of its checks ever
    # registered and its dimensions silently reported zero findings.
    "s22_frontend_contracts",
    # s23 states which benchmark laws the suite does NOT check. Without it the
    # 84-law gap was invisible, and a clean report read as "325/325 pass".
    "s23_law_coverage",
    # s24 covers the benchmark laws that were decidable from source but had no
    # check: test harness declaration, git hygiene, tsconfig strictness, layer
    # purity, compat shims.
    "s24_declared_laws",
]

IMPORT_ERRORS: dict[str, str] = {}

for _name in _MODULES:
    try:
        import_module(f"{__name__}.{_name}")
    except Exception as _exc:  # pragma: no cover
        IMPORT_ERRORS[_name] = f"{type(_exc).__name__}: {_exc}"


def import_failures() -> list[tuple[str, str]]:
    """Scanners that failed to import.

    A scanner that cannot import is not a scanner that found nothing. Reporting
    it here keeps the difference visible: without this, a broken scanner reduces
    its dimension to zero findings and the audit reads as a clean result.
    """
    return sorted(IMPORT_ERRORS.items())
