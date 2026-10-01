"""Finance Payroll Service — wraps hr payroll_service for finance domain.

This module provides payroll functions for the finance domain to avoid
cross-domain imports in routers (Law 6 compliance).
"""

from domains.hr.ports import PayrollEngine
