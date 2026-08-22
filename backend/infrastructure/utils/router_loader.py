"""Non-silent router loader for ``modules/*/routers/__init__.py`` packages.

This replaces the per-submodule ``try/except Exception: log + continue``
swallow that previously let a broken router submodule vanish from the app
with a single ``logger.error`` line (RESOLVER **P-SYS-01**, "silent-drop
hazard"). Per the architecture rules a modular monolith must keep serving
its healthy modules, so we still ``continue`` on a single bad submodule -
but we refuse to be *silent*: every failure is recorded with a full
traceback and surfaced in the boot summary via :func:`boot_summary`, which
``main._load_routers`` prints at startup. A dropped router can therefore
never pass unnoticed.

Stdlib only - this module must never import heavy application code, because
it runs at package-import time (during ``import main``).
"""
from __future__ import annotations

import importlib
import logging
import traceback
from typing import Dict, List, Tuple

_LOGGER = logging.getLogger("zozi.router_loader")

# package ("modules.<m>.routers") -> [(submodule_name, error_message), ...]
_FAILED: Dict[str, List[Tuple[str, str]]] = {}
# package -> error_message for a *whole-package* import failure
_PACKAGE_FAILED: Dict[str, str] = {}


def load_router_submodules(package, names, routers, public_routers):
    """Import each ``name`` under ``package`` and collect its ``router`` /
    ``public_router`` objects.

    Failures are logged loudly (ERROR + full traceback) and recorded in
    :data:`_FAILED`; healthy submodules still load. Returns the list of
    failed submodule names so callers can assert on it in tests.
    """
    failures: List[Tuple[str, str]] = []
    for _n in names:
        _mod = "%s.%s" % (package, _n)
        try:
            _m = importlib.import_module(_mod)
        except Exception as _e:  # noqa: BLE001
            _tb = traceback.format_exc()
            _LOGGER.error("ROUTER IMPORT FAILED: %s -> %s\n%s", _mod, _e, _tb)
            failures.append((_n, str(_e)))
            continue
        _r = getattr(_m, "router", None)
        if _r is not None:
            routers.append(_r)
        _pr = getattr(_m, "public_router", None)
        if _pr is not None:
            public_routers.append(_pr)
    if failures:
        _FAILED[package] = _FAILED.get(package, []) + failures
        _names = ", ".join(n for n, _ in failures)
        _LOGGER.error(
            "BOOT ROUTER FAILURES in %s: %d submodule(s) DROPPED -> [%s]",
            package, len(failures), _names,
        )
    return [n for n, _ in failures]


def record_package_failure(package: str, error: str) -> None:
    """Record a *whole-package* import failure (the package ``__init__`` itself raised)."""
    _PACKAGE_FAILED[package] = error
    _LOGGER.error("BOOT PACKAGE FAILURE: %s -> %s", package, error)


def get_failed_imports():
    """Mapping of package -> dropped submodule failures (empty == healthy)."""
    return _FAILED


def get_package_failures():
    """Mapping of package -> whole-package import error (empty == healthy)."""
    return _PACKAGE_FAILED


def boot_summary() -> str:
    """Aggregate boot summary of every dropped router. Empty string == healthy."""
    lines: List[str] = []
    for pkg, err in _PACKAGE_FAILED.items():
        lines.append("PACKAGE FAILURE %s: %s" % (pkg, err))
    for pkg, fails in _FAILED.items():
        names = ", ".join(n for n, _ in fails)
        lines.append("ROUTER FAILURES %s: %d dropped -> [%s]" % (pkg, len(fails), names))
    return "\n".join(lines)
