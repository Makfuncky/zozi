"""controllers.admin.suppliers controller.

Business logic is delegated to services.admin.suppliers_service (routers -> controllers -> services)."""

from services.admin.suppliers_service import (
    bulk_manage_suppliers, bulk_supplier_verification, get_all_suppliers, get_pending_suppliers, get_supplier_comparison, reject_supplier,
    verify_supplier
)

__all__ = [
    "bulk_manage_suppliers", "bulk_supplier_verification", "get_all_suppliers", "get_pending_suppliers", "get_supplier_comparison", "reject_supplier",
    "verify_supplier"
]
