"""Backward-compat shim — canonical location is providers/ai/image_ai_service.py.

Resolved lazily via __getattr__ + importlib.import_module so this infrastructure
module carries no static upward import (Law 1: arrows point down only).
"""
from __future__ import annotations

import importlib


_CANONICAL = "providers.ai.image_ai_service"


def __getattr__(name: str):
    mod = importlib.import_module(_CANONICAL)
    try:
        return getattr(mod, name)
    except AttributeError:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from None


def __dir__():
    mod = importlib.import_module(_CANONICAL)
    return sorted(
        set(dir(mod))
        - {"__name__", "__doc__", "__file__", "__loader__", "__spec__"}
    )
