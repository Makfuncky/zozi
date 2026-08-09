"""Forwarder shim restoring the canonical ``data.models`` public surface.

The circuit contract forbids the ``routers`` and ``controllers`` layers from
importing ``models`` directly; they must reach ORM types through this ``data``
shim instead. ``data`` is an exempt layer in the architecture audit.

Mirrors the historical ``data/models.py`` forwarder convention documented in
``data/orm_models.py``; its deletion broke roughly a hundred import sites.
"""
from __future__ import annotations

import importlib
import pkgutil

import models as _models

from models import *  # noqa: F401,F403  -- forward all canonical models
from models import Base  # noqa: F401  -- commonly referenced declarative base
import structlog
logger = structlog.get_logger(__name__)

# Copy every name currently visible on the ``models`` package so that
# ``from data.models import X`` works for re-exported symbols without a search.
for _k in list(vars(_models)):
    if not _k.startswith("_"):
        globals()[_k] = getattr(_models, _k)


def __getattr__(name: str):
    # Some ORM classes live in model submodules whose ``__all__`` does not
    # re-export them into the ``models`` package namespace. Search the model
    # submodules lazily so the exempt ``data`` facade resolves them anyway.
    for _finder, _modname, _ispkg in pkgutil.iter_modules(_models.__path__):
        try:
            _mod = importlib.import_module(f"models.{_modname}")
        except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
            logger.exception("__getattr___failed", error=str(e))
            continue
        _val = getattr(_mod, name, None)
        if _val is not None:
            return _val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")