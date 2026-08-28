"""Comms auth dependencies — wraps security domain auth functions.

This module provides auth functions for the comms domain to avoid
cross-domain imports in routers (Law 6 compliance).
"""

from domains.security.ports import require_roles
