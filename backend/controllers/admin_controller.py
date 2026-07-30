"""Backward-compatible re-exports from the admin subpackage.

Routers that still import from controllers.admin_controller will
continue to work. All business logic lives in controllers/admin/*.py.
"""
from controllers.admin import *  # noqa: F401, F403
