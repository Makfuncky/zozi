"""Migration re-export shim for the old controller module `suppliers_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from modules.admin.routers.admin import list_pending_suppliers, supplier_comparison

# Unresolved during migration: bulk_manage_suppliers_route, bulk_verify_suppliers_route, list_suppliers, reject_supplier_route, verify_supplier_route
