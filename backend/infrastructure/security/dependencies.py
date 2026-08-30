"""FastAPI auth dependencies — backward-compat shim.

Canonical implementation lives in
``domains.accounts.services.auth.security_dependencies``.
All auth flows through ``infrastructure.utils.auth`` (decode_token / verify_token).

This module uses lazy resolution to avoid a static upward import (Law 1).
"""
from __future__ import annotations

import importlib as _importlib

_SOURCE = "domains.accounts.services.auth.security_dependencies"

def __getattr__(name: str):
    mod = _importlib.import_module(_SOURCE)
    value = getattr(mod, name)
    # Ensure every resolved user is published to the rbac context var so that
    # feature/module gates (which read the current user from request context)
    # work for both ``Depends(...)`` and direct in-handler ``require_feature``
    # calls. Lazy import keeps the upward edge out of the static import graph.
    if name == "get_current_user":
        import functools

        _orig = value

        @functools.wraps(_orig)
        def _wrapped(*args, **kwargs):
            # Lazy import kept inside the call to avoid a circular import at
            # module load time (rbac.dependencies imports this shim).
            from rbac.dependencies import set_current_user

            user = _orig(*args, **kwargs)
            try:
                set_current_user(user)
            except Exception:
                pass
            return user

        value = _wrapped
    globals()[name] = value
    return value
