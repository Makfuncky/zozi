"""Declarative base shared by all ORM models.

This module re-exports the single canonical ``Base`` defined in the
``models`` package. Historically it defined a *separate, empty*
``DeclarativeBase`` which caused any code that imported
``from db.base import Base`` and introspected ``Base.metadata`` (the schema
audit utility, several services, and the test fixtures) to see zero tables.
All ORM model classes register themselves on ``models.Base``, so the two must
be the same object. ``models`` never imports ``db.base`` (it only depends on
``db.mixins``), so this re-export introduces no import cycle.
"""
from __future__ import annotations

from models import Base  # noqa: F401  -- single canonical declarative base
