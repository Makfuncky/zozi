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
    globals()[name] = value
    return value
