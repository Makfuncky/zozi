"""Backward-compat shim — canonical implementation is kernel/constants.py."""
from kernel.constants import *  # noqa: F401,F403
from kernel.constants import _ADMIN_DEFAULT_PAGE_SIZE, _ADMIN_MAX_PAGE_SIZE  # Explicit import for underscore-prefixed names
