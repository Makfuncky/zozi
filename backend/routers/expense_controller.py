"""Expense router.

Thin delegating router for ``controllers.finance.expense_controller`` (covers expense,
financial, payroll, treasury and contractor-milestones surfaces).

NOTE: the referenced controller module does not yet exist; this router owns its own
empty ``APIRouter`` so the app boots. Implement
``controllers.finance.expense_controller`` and replace the import once ready.
"""
from fastapi import APIRouter

router = APIRouter()
__router_prefix__ = "/api/v1"

__all__ = ["router"]
