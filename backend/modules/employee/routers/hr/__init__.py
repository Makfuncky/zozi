"""Split router package — originally hr.py."""

from hr.router import router  # noqa: F401
import hr.employees_part1_p1  # noqa: F401
import hr.employees_part1_p2  # noqa: F401
import hr.employees_part2  # noqa: F401
import hr.ess  # noqa: F401
import hr.hierarchy  # noqa: F401
import hr.hr_dashboard  # noqa: F401
import hr.lms  # noqa: F401
import hr.okr  # noqa: F401
import hr.payroll  # noqa: F401
import hr.performance  # noqa: F401
import hr.shift_handover  # noqa: F401
import hr.succession  # noqa: F401

__all__ = ["router"]
