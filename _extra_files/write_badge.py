content = '''"""Supplier badge controller surface.

Thin re-export layer over the canonical badge service so that
``controllers.supplier.badge`` keeps a stable public surface while the real
implementation lives in ``services.supplier.supplier_badge_service``.
"""
from __future__ import annotations

from services.supplier.supplier_badge_service import (
    admin_set_supplier_badge,
    compute_credibility_score,
    list_supplier_badge_billing_history,
    list_supplier_badge_catalog,
    purchase_supplier_badge,
    record_badge_billing_payment,
    refresh_supplier_badge,
    run_badge_recalculation_cycle,
)

__all__ = [
    "admin_set_supplier_badge",
    "compute_credibility_score",
    "list_supplier_badge_billing_history",
    "list_supplier_badge_catalog",
    "purchase_supplier_badge",
    "record_badge_billing_payment",
    "refresh_supplier_badge",
    "run_badge_recalculation_cycle",
]
'''
with open("backend/controllers/supplier/badge.py", "w", encoding="utf-8") as fh:
    fh.write(content)
print("wrote badge.py")
