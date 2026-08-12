"""Backward-compatible re-exports from the governance domain package.

The governance route ``router`` (APIRouter) is defined in the legacy
hand-written router ``routers/governance_package.py``; re-export it here so the
thin delegating router ``routers/operational_controller.py`` can pull ``router``
from this module without depending on ``routers`` directly.
"""
from controllers.governance import *  # noqa: F401, F403
from routers.governance_package import router  # noqa: F401

__all__ = ["router"]
