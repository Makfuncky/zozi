"""Backward-compat shim — canonical location is infrastructure/storage/storage.py."""

import importlib
from typing import Any

_canonical_module = None


def __getattr__(name: str) -> Any:
    """Lazily resolve public names from the canonical storage module."""
    global _canonical_module
    if _canonical_module is None:
        _canonical_module = importlib.import_module("infrastructure.storage.storage")
    try:
        return getattr(_canonical_module, name)
    except AttributeError:
        raise AttributeError(
            f"module 'infrastructure.utils.media_storage' has no attribute {name!r}"
        )
