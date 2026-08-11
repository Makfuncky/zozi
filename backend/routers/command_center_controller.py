"""Command-center router.

Thin delegating router for ``controllers.governance.command_center_controller``. Routes are
defined with absolute paths inside the controller; mounted under ``/api/v1`` so
they surface as ``/api/v1/admin/command-center/...``.
"""
from controllers.governance.command_center_controller import router
__router_prefix__ = "/api/v1"

__all__ = ["router"]
