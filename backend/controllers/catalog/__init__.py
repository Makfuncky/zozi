"""Catalog domain controllers (LAYER 3).

Orchestrates ``services.catalog.*`` and shapes HTTP responses. Routers import
from here; nothing in this package touches the SQLAlchemy session directly.

Explicit package marker — previously this folder held Python files with no
``__init__.py`` (audit P5), so ``controllers.catalog`` was only importable by
accident via namespace packages.
"""
from __future__ import annotations
import structlog
logger = structlog.get_logger(__name__)

__all__ = [
    "category_admin_controller",
    "product_controller",
    "product_moderation_controller",
]
