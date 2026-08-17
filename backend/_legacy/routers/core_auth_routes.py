"""Auth router.

Re-exports the canonical `get_current_user` dependency so that
`from routers.core_auth_routes import get_current_user` continues to work.
The dependency itself lives in `controllers.security.auth_controller`.
"""
from fastapi import APIRouter

from controllers.security.auth_controller import get_current_user

router = APIRouter(prefix="/api/v1")

