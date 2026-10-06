"""Law 135 gate: no module router may be invisible to FastAPI.

``modules/{m}/routers/__init__.py`` imports every router module in a
``try/except`` and, on failure, only emits ``Skipping router <name>: ...`` and
continues. ``main.py::_load_routers`` has the same shape one level up. The
consequence is that a broken module-level ``from domains.finance.ports import
...`` does not fail the build or the boot: the whole router silently vanishes
and every endpoint it owns answers 404 in production while ``/health`` keeps
reporting 200.

This gate closes that hole. It walks every ``.py`` file under
``backend/modules/*/routers/``, resolves it to its dotted module path, and
``importlib.import_module``s it. Any ``ImportError`` / ``AttributeError`` (or
any other exception raised at import time) fails the test and names the module
and the original error, so the failure is attributable to one file rather than
to "boot went weird".

Laws: Law 135 (all router files listed in ``routers/__init__.py``; an
unregistered router is dead code), Law 81 (health checks must reflect real
state -- a router that never loaded is not a healthy app), Law 98 (no circular
imports -- an import cycle shows up here as an ``ImportError``), Law 15
(every HTTP endpoint lives in a module router file named after the domain).

Scanning rules
--------------
* Recursive: a non-recursive ``routers/*.py`` glob silently misses subpackage
  routers such as ``modules/employee/routers/hr/__init__.py``, which is a real
  router module carrying ``router = APIRouter(...)``.
* ``routers/__init__.py`` is skipped. It is the aggregator, not a router, and
  its own import is what the failing child routers are hiding behind.
* ``__init__.py`` *inside* a subpackage is not skipped -- its dotted path is
  the router module itself.
* ``__pycache__`` and any non-``.py`` file are ignored.

No baseline and no xfail: the whole point of BOOT2-004 is that a baseline is
how two dead routers survived. Every broken router is reported.
"""
from __future__ import annotations

import importlib
import sys
from pathlib import Path

# ``backend/`` -- the directory that must be importable for ``modules.*`` to
# resolve. Derived from this file so the gate works from any pytest rootdir.
BACKEND = Path(__file__).resolve().parents[2]
MODULES_DIR = BACKEND / "modules"

# Directory names that never hold importable router sources.
_IGNORED_DIRS = {"__pycache__", ".pytest_cache"}


def _iter_router_module_names() -> list[str]:
    """Return the dotted module name of every router module under ``modules/``.

    ``modules/{m}/routers/{d}.py``            -> ``modules.{m}.routers.{d}``
    ``modules/{m}/routers/{sub}/__init__.py`` -> ``modules.{m}.routers.{sub}``

    Raises ``AssertionError`` if ``modules/`` or its ``routers/`` directories
    cannot be located -- a scan that silently finds nothing would make this
    gate enforce nothing (the failure mode Law 70 exists to prevent).
    """
    assert MODULES_DIR.is_dir(), (
        f"modules/ not found at {MODULES_DIR}. The Law 135 router gate cannot "
        "scan anything; fix BACKEND resolution before trusting a green run."
    )
    module_dirs = sorted(
        child.name
        for child in MODULES_DIR.iterdir()
        if child.is_dir() and not child.name.startswith(("_", ".")) and (child / "routers").is_dir()
    )
    assert module_dirs, (
        f"No modules/*/routers/ directory found under {MODULES_DIR}. The Law 135 "
        "router gate would enforce nothing."
    )

    names: list[str] = []
    for module_name in module_dirs:
        routers_dir = MODULES_DIR / module_name / "routers"
        for path in sorted(routers_dir.rglob("*.py")):
            if any(part in _IGNORED_DIRS for part in path.parts):
                continue
            relative = path.relative_to(routers_dir)
            parts = list(relative.parts)
            if parts[-1] == "__init__.py":
                if len(parts) == 1:
                    # routers/__init__.py -- the aggregator, not a router.
                    continue
                parts = parts[:-1]
            else:
                stem = parts[-1][: -len(".py")]
                parts[-1] = stem
            names.append(".".join(["modules", module_name, "routers", *parts]))
    return names


def test_every_module_router_imports() -> None:
    """Every ``modules/*/routers/*.py`` must import cleanly.

    A router that cannot be imported is dead code: ``main.py`` swallows the
    error, the endpoints answer 404, and ``/health`` still says 200.
    """
    if str(BACKEND) not in sys.path:
        sys.path.insert(0, str(BACKEND))

    names = _iter_router_module_names()
    assert names, "No router modules discovered -- the scan found nothing to gate."

    failures: list[str] = []
    for name in names:
        try:
            importlib.import_module(name)
        except ImportError as exc:
            # The classic case: a module-level ``from domains.<d>.ports import X``
            # where ``X`` is not registered in that domain's ports.py.
            failures.append(
                f"  {name}\n      -> {type(exc).__name__}: {exc}\n"
                "      -> main.py logs 'Skipping router ...' and boots anyway; every\n"
                "         endpoint owned by this router returns 404 (Law 135 / Law 81)."
            )
        except AttributeError as exc:
            # A lazy ``__getattr__`` in a ports.py that falls through, or a
            # module-level attribute access on a name that is not defined.
            failures.append(
                f"  {name}\n      -> {type(exc).__name__}: {exc}\n"
                "      -> a module-level attribute lookup failed; the router never loads."
            )
        except Exception as exc:  # noqa: BLE001 -- any import-time failure is a dead router
            failures.append(
                f"  {name}\n      -> {type(exc).__name__}: {exc}\n"
                "      -> unexpected error raised while importing the router module."
            )

    assert not failures, (
        f"{len(failures)} of {len(names)} module router module(s) failed to import. "
        "Each one is invisible to FastAPI (Law 135) and invisible to /health "
        "(Law 81). Broken routers:\n"
        + "\n".join(failures)
    )