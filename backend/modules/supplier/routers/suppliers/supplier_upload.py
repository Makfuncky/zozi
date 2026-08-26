# === From supplier_upload.py ===
"""
Re-export shim for the supplier upload (BG A/B testing) router.

The canonical BG-strategy A/B testing routes now live in
``modules.supplier.routers.supplier_supplier_upload``. This module previously
held a duplicated near-copy; it is retained only as a re-export
(MERGE-NOT-DELETE policy — see RESOLVER.md §7 S1).
"""
from .supplier_supplier_upload import *  # noqa: F401,F403
from .supplier_supplier_upload import router  # noqa: F401
from rbac.dependencies import require_feature

