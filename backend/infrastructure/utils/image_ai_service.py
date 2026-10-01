"""Backward-compat shim — canonical location is providers/ai/image_ai_service.py."""

import sys

_CANONICAL = "providers.ai.image_ai_service"


def _get_canonical():
    import importlib

    return importlib.import_module(_CANONICAL)


_mod = sys.modules[__name__]
_real = _get_canonical()
for _attr in ("__name__", "__doc__", "__file__", "__loader__", "__spec__"):
    try:
        setattr(_mod, _attr, getattr(_real, _attr))
    except AttributeError:
        pass
del _mod, _real, _attr


def __getattr__(name: str):
    mod = _get_canonical()
    try:
        return getattr(mod, name)
    except AttributeError:
        raise AttributeError(
            f"module {__name__!r} has no attribute {name!r}"
        ) from None


def __dir__():
    mod = _get_canonical()
    return sorted(
        set(dir(mod))
        - {"__name__", "__doc__", "__file__", "__loader__", "__spec__"}
    )
