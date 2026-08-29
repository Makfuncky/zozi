"""Backward-compat shim — re-export auth dependencies."""
from __future__ import annotations


def __getattr__(name: str):
    from domains.accounts.services.auth import security_dependencies
    return getattr(security_dependencies, name)
