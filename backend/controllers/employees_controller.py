"""Re-export employees controller for backward compatibility."""
from controllers.hr.employees_controller import *  # noqa: F401, F403

__all__ = [
    "get_employee",
    "get_employees",
    "create_employee",
    "update_employee",
    "delete_employee",
    "list_employees",
]