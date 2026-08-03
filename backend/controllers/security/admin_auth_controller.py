"""Admin authentication and authorization dependencies.

Backward-compatible re-exports for importers that reference the old
controllers.admin.auth path.  Canonical modules live in
controllers/security/auth.py and controllers/security/auth_controller.py.
"""
from controllers.security.auth import (  # noqa: F401
    get_current_admin,
    require_admin,
    require_admin_2fa_enabled,
    require_admin_2fa_verified,
    require_roles,
    require_permission,
    require_country_access,
)
from controllers.security.auth_controller import get_current_user  # noqa: F401
