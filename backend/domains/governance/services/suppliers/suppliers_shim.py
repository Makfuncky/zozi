"""services.suppliers re-exports for HTTP routers (merge shim).

The canonical admin-supplier review/management functions live in
``admin_supplier_review_service``; this thin shim re-exports them under the
historical ``suppliers`` namespace so legacy importers keep working.
"""

from __future__ import annotations

from domains.suppliers.services.admin_supplier_review_service import (
    activate_supplier,
    approve_supplier_kyc,
    bulk_restore_suppliers,
    bulk_supplier_action,
    get_supplier_by_country,
    list_all_suppliers,
    list_all_suppliers_frontend,
    list_pending_kyc_suppliers,
    list_suppliers_by_country,
    list_suppliers_global,
    refresh_supplier_badge,
    reject_supplier_kyc,
    restore_supplier_frontend,
    suspend_supplier,
    update_supplier_by_country,
)

__all__ = [
    "activate_supplier",
    "approve_supplier_kyc",
    "bulk_restore_suppliers",
    "bulk_supplier_action",
    "get_supplier_by_country",
    "list_all_suppliers",
    "list_all_suppliers_frontend",
    "list_pending_kyc_suppliers",
    "list_suppliers_by_country",
    "list_suppliers_global",
    "refresh_supplier_badge",
    "reject_supplier_kyc",
    "restore_supplier_frontend",
    "suspend_supplier",
    "update_supplier_by_country",
]
