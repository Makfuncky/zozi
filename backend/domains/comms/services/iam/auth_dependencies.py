"""Comms auth dependencies — wraps security domain auth functions.

This module provides auth functions for the comms domain to avoid
cross-domain imports in routers (Law 6 compliance).
"""

from domains.security.services.iam.security_dependencies import require_roles
