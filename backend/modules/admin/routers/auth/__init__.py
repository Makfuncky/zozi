"""Auth stub"""
from infrastructure.utils.dependencies import require_admin, get_current_user  # noqa: F401


def require_permission(permission: str, user: dict | None = None):
    return True
