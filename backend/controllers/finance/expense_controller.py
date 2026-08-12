"""Backward-compatible re-exports from the finance domain package.

The finance route ``router`` (APIRouter) is defined in the legacy hand-written
router ``routers/finance_package.py``; re-export it here so the thin delegating
router ``routers/expense_controller.py`` can pull ``router`` from this module
without depending on ``routers`` directly.
"""
from controllers.finance import *  # noqa: F401, F403
from routers.finance_package import router  # noqa: F401

__all__ = ["router"]
