"""Backward-compat shim — canonical location is infrastructure/storage/storage.py."""
import importlib

_CANONICAL = "infrastructure.storage.storage"


def __getattr__(name: str):
    module = importlib.import_module("infrastructure.storage.storage")
    try:
        return getattr(module, name)
    except AttributeError:
        raise AttributeError(f"module 'infrastructure.storage.storage' has no attribute {name!r}")
