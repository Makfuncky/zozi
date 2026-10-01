r"""P-SYS-01 proof: a broken router submodule must be recorded + surfaced,
never silently swallowed.

Run:  PYTHONPATH=D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend python -m pytest tests/test_router_loader_psys01.py -q
"""
import sys
import types

from fastapi import APIRouter

from infrastructure.utils.router_loader import (
    boot_summary,
    get_failed_imports,
    get_package_failures,
    load_router_submodules,
    record_package_failure,
)


def _make_pkg(pkg_name):
    if pkg_name not in sys.modules:
        sys.modules[pkg_name] = types.ModuleType(pkg_name)
    good = types.ModuleType(pkg_name + ".good")
    good.router = APIRouter()
    good.public_router = APIRouter()
    sys.modules[pkg_name + ".good"] = good
    # ".bad" intentionally NOT registered -> import_module raises


def _cleanup(pkg):
    for k in list(sys.modules):
        if k == pkg or k.startswith(pkg + "."):
            del sys.modules[k]


def test_load_records_failure_loudly():
    pkg = "psys01_pkg"
    _make_pkg(pkg)
    routers, public_routers = [], []
    failed = load_router_submodules(pkg, ["good", "bad"], routers, public_routers)
    # healthy submodule still collected (resilience preserved)
    assert len(routers) == 1 and len(public_routers) == 1
    # broken submodule recorded (non-silent)
    assert "bad" in failed
    assert pkg in get_failed_imports()
    assert any(n == "bad" for n, _ in get_failed_imports()[pkg])
    # boot summary surfaces it
    summary = boot_summary()
    assert "bad" in summary and pkg in summary
    _cleanup(pkg)


def test_clean_load_records_nothing():
    pkg = "psys01_clean"
    _make_pkg(pkg)
    routers, public_routers = [], []
    failed = load_router_submodules(pkg, ["good"], routers, public_routers)
    assert failed == []
    assert pkg not in get_failed_imports()
    _cleanup(pkg)


def test_package_failure_recorded():
    record_package_failure("modules.x.routers", "boom")
    assert get_package_failures().get("modules.x.routers") == "boom"
    assert "modules.x.routers" in boot_summary()
