"""Migration re-export shim for the old controller module `supplier_health_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from domains.accounts.services.supplier_health_service import get_supplier_health, list_supplier_health
