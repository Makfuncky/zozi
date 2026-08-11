"""Expense router.

Thin delegating router for ``controllers.finance.expense_controller`` (covers expense,
financial, payroll, treasury and contractor-milestones surfaces).
"""
from controllers.finance.expense_controller import router
__router_prefix__ = "/api/v1"

__all__ = ["router"]
