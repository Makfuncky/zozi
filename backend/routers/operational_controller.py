"""Operational router.

Thin delegating router for ``controllers.governance.operational_controller`` (employee
leave-balance/expenses/assets and compliance work-hours/report/overtime).
"""
from controllers.governance.operational_controller import router
__router_prefix__ = "/api/v1"

__all__ = ["router"]
