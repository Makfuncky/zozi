"""P-SYS-04 verification: every module exposes a live serializer surface.

Resolves ARCHITECTURE_DIAGRAM.md §3 (per-actor view models live in
``modules/{m}/serializers/``) — previously 4 of 5 module serializer packages were
empty (0 lines), so they were dead surfaces. This test proves each package imports
cleanly and exposes its per-actor ``XView`` model + the shared auth schemas.

Kept in ``zozi/tests`` per the migration restrictions (temp/test files live here).
"""
from __future__ import annotations

import importlib

MODULE_SERIALIZERS = {
    "customer": "modules.customer.serializers",
    "supplier": "modules.supplier.serializers",
    "logistics": "modules.logistics.serializers",
    "admin": "modules.admin.serializers",
    "employee": "modules.employee.serializers",
}


def test_all_module_serializers_import_and_expose_view():
    for module, dotted in MODULE_SERIALIZERS.items():
        mod = importlib.import_module(dotted)
        # shared auth schemas must be re-exported from the surface
        assert hasattr(mod, "UserOut"), f"{module}: missing UserOut"
        assert hasattr(mod, "TokenResponse"), f"{module}: missing TokenResponse"
        assert hasattr(mod, "RegisterRequest"), f"{module}: missing RegisterRequest"
        # per-actor view model must exist (diagram §3)
        view_name = f"{module.capitalize()}View"
        assert hasattr(mod, view_name), f"{module}: missing {view_name}"
        view = getattr(mod, view_name)
        assert issubclass(view, object)
