"""Employees API Router (re-export from HR domain).

All employee-related endpoints live in routers/hr/.
"""
from routers.hr.hr import router
__all__ = ["router"]