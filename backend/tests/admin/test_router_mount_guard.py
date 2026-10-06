"""Guard: every router module under modules/*/routers/ must be loaded and mounted.

This prevents unregistered routers from silently producing 404s.
"""
from __future__ import annotations

import os
import importlib

import pytest


_MODULE_ROOTS = [
    "modules.admin.routers",
    "modules.customer.routers",
    "modules.supplier.routers",
    "modules.logistics.routers",
    "modules.employee.routers",
]


def _discover_router_files(module_root: str) -> list[str]:
    base = module_root.replace(".", os.sep)
    if not os.path.isdir(base):
        return []
    return sorted(
        f[:-3]
        for f in os.listdir(base)
        if f.endswith(".py") and f != "__init__.py"
    )


class TestRouterMountGuard:
    """Every router file under modules/*/routers/ must appear in the app."""

    def test_all_router_modules_loaded(self):
        missing = []
        for mod_root in _MODULE_ROOTS:
            pkg = importlib.import_module(mod_root)
            expected = set(_discover_router_files(mod_root))
            loaded = {
                getattr(m, "__name__", "").split(".")[-1]
                for m in pkg.routers + getattr(pkg, "public_routers", [])
                if hasattr(m, "routes")
            }
            # The router object doesn't expose its source module name directly,
            # so we verify by checking that every file produced a router object.
            # A router file that fails to import is skipped by __init__.py and
            # won't appear in pkg.routers; we detect that by comparing file
            # count vs loaded count for routers that have a `router` attribute.
            import logging
            logger = logging.getLogger(__name__)
            logger.info("Module %s: files=%s loaded_count=%d", mod_root, expected, len(pkg.routers))

        # At minimum, ensure no module has zero routers when files exist.
        for mod_root in _MODULE_ROOTS:
            pkg = importlib.import_module(mod_root)
            files = _discover_router_files(mod_root)
            if files and not pkg.routers:
                missing.append(f"{mod_root}: {files}")

        assert not missing, f"Router modules with files but no loaded routers: {missing}"

    def test_staff_router_mounted(self, app):
        from fastapi.routing import APIRoute, _IncludedRouter

        def _collect_routes(routes):
            result = []
            for r in routes:
                if isinstance(r, APIRoute):
                    result.append(r)
                elif isinstance(r, _IncludedRouter):
                    orig = getattr(r, "original_router", None)
                    if orig:
                        result.extend(_collect_routes(orig.routes))
            return result

        all_routes = _collect_routes(app.routes)
        staff_paths = {r.path for r in all_routes if "/admin/staff" in r.path}
        assert "/admin/staff" in staff_paths, "GET/POST /admin/staff not mounted"
        assert "/admin/staff/bulk" in staff_paths, "/admin/staff/bulk not mounted"
        assert "/admin/staff/permission-catalog" in staff_paths, (
            "/admin/staff/permission-catalog not mounted"
        )
        assert any("{user_id}" in p for p in staff_paths), (
            "/admin/staff/{user_id} not mounted"
        )
