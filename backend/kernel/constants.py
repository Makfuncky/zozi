"""Backward-compat shim — canonical implementation lives in infrastructure/utils/constants.py.

All constants here are business-specific (RBAC roles, statuses, pagination caps,
finance account codes, upload limits). Kernel/ must contain only pure business
primitives (money, currency, numbering, country, period), so this file was
relocated to infrastructure/utils/ where shared application constants belong.
Re-exported here so legacy imports keep working.
"""
from infrastructure.utils.constants import *  # noqa: F401,F403
from infrastructure.utils.constants import (  # noqa: F401
    _ADMIN_DEFAULT_PAGE_SIZE,
    _ADMIN_MAX_PAGE_SIZE,
)
