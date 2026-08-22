"""Country communications read service - re-export shim.

The canonical implementation lives in
``domains.country.services.country_communications_read_service`` (synchronous,
``db: Session``-parameterised service functions). This module previously held an
async ``Depends(get_db)`` duplicate of the same four read functions and had no
importers. It is retained as a single-source re-export shim (MERGE-NOT-DELETE
policy, aligned with P4/P6) so any legacy path keeps resolving with zero edits.
"""
from __future__ import annotations

from domains.country.services.country_communications_read_service import list_cross_border_sessions, list_legal_contracts, list_warehouses, list_partner_locations

__all__ = [
    "list_cross_border_sessions",
    "list_legal_contracts",
    "list_warehouses",
    "list_partner_locations",
]