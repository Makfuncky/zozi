"""Canonical ``models.orders`` domain package.

The previous flat ``models/orders.py`` was promoted to this package
(``models/orders/order_entities.py``) to satisfy the AI File Placement
Contract (``backend/models/`` must be organised as domain folders) and to
reduce the coupling of ``models/__init__.py`` (god-module MET5).

``Base`` is re-exported from the parent ``models`` package so the submodule
can keep using the relative ``from . import Base`` idiom.
"""
from __future__ import annotations

from .. import Base

from .order_entities import *  # noqa: F401,F403
