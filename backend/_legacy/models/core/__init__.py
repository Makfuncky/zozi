"""Canonical ``models.core`` package.

Forwards the core ORM surface (chat, audit, address, etc.) from the
``models.comms`` package so ``models.core.*`` and ``models.comms.core.*``
resolve to the same class objects (avoids duplicate-table collisions).

This module previously lived at ``models/core.py``; promoting it to a package
directory resolves the file-vs-package name collision that broke
``models._exports`` (``from .core.user import *``).
"""
from __future__ import annotations

from models.comms.core import *  # noqa: F401,F403
