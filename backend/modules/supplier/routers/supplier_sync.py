"""
Re-export shim for the supplier sync router.

The canonical supplier sync routes now live in
``modules.supplier.routers.supplier_supplier_sync``. This module previously held
a duplicated near-copy of that router; it is retained only as a re-export so any
lingering imports keep working (MERGE-NOT-DELETE policy — see RESOLVER.md §7 S1).
"""
from .supplier_supplier_sync import *  # noqa: F401,F403
from .supplier_supplier_sync import router  # noqa: F401
from rbac.dependencies import require_feature
