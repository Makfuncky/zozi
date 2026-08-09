"""Declarative base shared by all ORM models.

Re-exports the canonical ``Base`` from the ``models`` package so that
``db.base.Base`` and ``models.Base`` are the *same* class with a single
shared ``MetaData``.  This ensures ``Base.metadata.create_all()`` is
aware of every table registered via the ``models`` package.
"""
from __future__ import annotations

from models import Base

__all__ = ["Base"]
