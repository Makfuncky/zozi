"""Services package.

Domain services live in subdirectories (ai/, finance/, hr/, etc.).
Some cross-cutting helpers are exported here for convenience.
"""
from services.core.write_helpers import (
    add_and_flush,
    commit_and_refresh,
    commit_only,
    flush_only,
    refresh_only,
    delete_only,
    rollback_only,
)
__all__ = [
    "add_and_flush",
    "commit_and_refresh",
    "commit_only",
    "flush_only",
    "refresh_only",
    "delete_only",
    "rollback_only",
]

import os as _os
import sys as _sys
import importlib as _importlib
from importlib.machinery import ModuleSpec
from importlib.abc import MetaPathFinder, Loader as _Loader

_PKG_DIR = _os.path.dirname(__file__)
_SUBDOMAINS = (
    "admin", "ai", "analytics", "audit", "catalog", "commerce",
    "communication", "core", "country", "finance", "hr", "location",
    "logistics", "media", "orders", "payments", "security", "supplier",
    "treasury", "uploads",
)


class _LegacyFlatServiceFinder(MetaPathFinder):
    """Resolve legacy flat ``services.<name>`` imports to domain subdirectories.

    When ``services/<name>.py`` does not exist as a flat file, this finder
    searches the domain subpackages and redirects the import to
    ``services.<domain>.<name>``.  This lets stale call sites
    (``from services.coi_service import ...``) keep working after modules
    were moved into subdirectories.
    """

    _pkg_dir = _PKG_DIR
    _subdomains = _SUBDOMAINS

    def find_spec(self, fullname, path, target=None):
        if not fullname.startswith("services.") or fullname.count(".") != 1:
            return None
        flat_name = fullname.split(".", 1)[1]
        if _os.path.isfile(_os.path.join(self._pkg_dir, flat_name + ".py")):
            return None
        for sub in self._subdomains:
            candidate = _os.path.join(self._pkg_dir, sub, flat_name + ".py")
            if _os.path.isfile(candidate):
                return self._make_spec(fullname, sub, flat_name)
        return None

    def _make_spec(self, fullname, sub, flat_name):
        real_name = f"services.{sub}.{flat_name}"
        class _LoaderShim(_Loader):
            def create_module(self, spec):
                return None
            def exec_module(self, module):
                real_mod = _sys.modules.get(real_name)
                if real_mod is None:
                    real_mod = _importlib.import_module(real_name)
                module.__dict__.update(real_mod.__dict__)
                module.__file__ = real_mod.__file__
                module.__package__ = real_mod.__package__
                module.__spec__ = real_mod.__spec__
                module.__loader__ = self
        return ModuleSpec(fullname, _LoaderShim(), origin=f"shim:{real_name}")


_sys.meta_path.insert(0, _LegacyFlatServiceFinder())
