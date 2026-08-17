"""Operational router.

Thin delegating router for ``controllers.governance.operational_controller`` (employee
leave-balance/expenses/assets and compliance work-hours/report/overtime).

NOTE: the referenced controller module does not yet exist; this router owns its own
empty ``APIRouter`` so the app boots. Implement
``controllers.governance.operational_controller`` and replace the import once ready.
"""
from fastapi import APIRouter

router = APIRouter()
__router_prefix__ = "/api/v1"

__all__ = ["router"]
