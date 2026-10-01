"""Backward-compat shim — re-export auth dependencies.

Resolved lazily via __getattr__ + importlib.import_module so this infrastructure
module carries no static upward import (Law 1: arrows point down only).
"""
from __future__ import annotations

import importlib


def __getattr__(name: str):
    _mod = importlib.import_module("domains.accounts.services.auth.security_dependencies")
    return getattr(_mod, name)
