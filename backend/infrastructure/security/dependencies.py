"""FastAPI auth dependencies — backward-compat shim.

Canonical implementation lives in
``domains.accounts.services.auth.security_dependencies``.
All auth flows through ``infrastructure.utils.auth`` (decode_token / verify_token).
"""
from __future__ import annotations

from domains.accounts.services.auth.security_dependencies import *  # noqa: F401,F403

# Re-exported symbols preserve backward compatibility for any
# ``from infrastructure.security.dependencies import <name>`` callers.
