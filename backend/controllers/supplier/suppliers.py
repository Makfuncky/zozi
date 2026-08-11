"""controllers.supplier.suppliers controller.

Business logic is delegated to services.supplier.suppliers_service (routers -> controllers -> services)."""

from services.supplier.suppliers_service import (
    _build_list_page_payload, bulk_manage_suppliers, bulk_supplier_verification, get_all_suppliers, get_pending_suppliers, get_supplier_comparison,
    logger, reject_supplier, verify_supplier
)

__all__ = [
    "_build_list_page_payload", "bulk_manage_suppliers", "bulk_supplier_verification", "get_all_suppliers", "get_pending_suppliers", "get_supplier_comparison",
    "logger", "reject_supplier", "verify_supplier"
]
