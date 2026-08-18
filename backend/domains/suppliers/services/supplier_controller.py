"""Migration re-export shim for the old controller module `supplier_controller`.
Symbols resolve to their real domain/infra homes.
"""
from __future__ import annotations

from domains.suppliers.services.supplier_service import _process_image_with_tools, process_product_image
