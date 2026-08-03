"""Authentication API Router and dependencies (re-export from security domain).

All existing `from routers.auth import get_current_user` imports continue to work
unchanged. The actual implementation lives in controllers.security.auth_controller.
"""
from data.routers_security_auth import router, LoginRequest, RefreshRequest
from controllers.security.auth_controller import get_current_user
__all__ = ["router", "LoginRequest", "RefreshRequest", "get_current_user"]