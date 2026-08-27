"""ORM model registry facade.

Domain models are imported directly from their canonical homes
(e.g. ``from domains.catalog.models.products import Product``).

This module intentionally does NOT walk the ``domains`` package —
infrastructure must not import domains (Law 1: modules → domains → infrastructure).
"""
from __future__ import annotations

__all__ = []
