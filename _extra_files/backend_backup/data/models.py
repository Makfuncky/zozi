"""Forwarder shim restoring the canonical ``data.models`` public surface.

The circuit contract forbids the ``routers`` and ``controllers`` layers from
importing ``models`` directly; they must reach ORM types through this ``data``
shim instead. ``data`` is an exempt layer in the architecture audit.

Mirrors the historical ``data/models.py`` forwarder convention documented in
``data/orm_models.py``; its deletion broke roughly a hundred import sites.
"""
from __future__ import annotations

from models import *  # noqa: F401,F403  -- forward all canonical models
from models import Base  # noqa: F401  -- commonly referenced declarative base
