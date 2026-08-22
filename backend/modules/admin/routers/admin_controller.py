"""Backward-compat re-export for legacy ``from modules.admin.routers.admin_controller import ...``.

The ``admin_controller`` API was fissioned into ``domains.governance.services.admin_controller``
during the NEW_STRUCTURE migration. This module keeps legacy router/service imports working.
"""
from domains.governance.services.admin_controller import *  # noqa: F401,F403
from rbac.dependencies import require_feature
