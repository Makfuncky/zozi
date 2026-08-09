"""``models.media`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat module ``models/media_models.py`` (preserved for backward
compatibility); this package forwards to it so ``models.media.MediaAsset``
and ``models.MediaAsset`` resolve to the same class object (no duplicate
tables).
"""
from __future__ import annotations

from models.media_models import *  # noqa: F401,F403
