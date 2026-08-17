"""controllers.hr.lms_controller controller.

Business logic is delegated to services.hr.lms_service (routers -> controllers -> services)."""

from services.hr.lms_service import (
    assign_training, check_permission_lock, create_training_module, get_training_progress, verify_training_completion
)

__all__ = [
    "assign_training", "check_permission_lock", "create_training_module", "get_training_progress", "verify_training_completion"
]
