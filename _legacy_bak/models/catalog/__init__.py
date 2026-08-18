"""``models.catalog`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat module ``models/products.py`` (preserved for backward compatibility);
this package forwards to it so ``models.catalog.Product`` and
``models.Product`` resolve to the same class object (no duplicate tables).
"""
from __future__ import annotations

from _legacy.models.products import *  # noqa: F401,F403
