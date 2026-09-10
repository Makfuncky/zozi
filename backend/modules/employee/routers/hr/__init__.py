"""Employee HR sub-router package.

Composed of thin sub-routers (Law 2 — no business logic). Each sub-router file
stays under 150 lines and delegates to ``domains/hr/services`` exclusively.
"""
from fastapi import APIRouter

from .offices import router as offices_router
from .employees import router as employees_router
from .attendance import router as attendance_router
from .leaves import router as leaves_router
from .ess import router as ess_router
from .hierarchy import router as hierarchy_router
from .matrix import router as matrix_router
from .approval import router as approval_router
from .lms import router as lms_router
from .payroll import router as payroll_router
from .performance import router as performance_router
from .succession import router as succession_router
from .health import router as health_router

router = APIRouter(prefix="/api/v1/employee/hr", tags=["employee", "hr"])
router.include_router(offices_router)
router.include_router(employees_router)
router.include_router(attendance_router)
router.include_router(leaves_router)
router.include_router(ess_router)
router.include_router(hierarchy_router)
router.include_router(matrix_router)
router.include_router(approval_router)
router.include_router(lms_router)
router.include_router(payroll_router)
router.include_router(performance_router)
router.include_router(succession_router)
router.include_router(health_router)

__all__ = ["router"]