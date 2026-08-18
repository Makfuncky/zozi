"""controllers.hr.lms_controller controller.

Business logic is delegated to services.hr.lms_service (routers -> controllers -> services)."""

from domains.hr.services.lms_service import assign_training
from domains.hr.services.lms_service import check_permission_lock
from domains.hr.services.lms_service import create_training_module
from domains.hr.services.lms_service import get_training_progress
from domains.hr.services.lms_service import verify_training_completion

__all__ = [
    "assign_training", "check_permission_lock", "create_training_module", "get_training_progress", "verify_training_completion"
]
