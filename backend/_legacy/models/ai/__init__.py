"""``models.ai`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat module ``models/ai_upload.py`` (preserved for backward compatibility);
this package forwards to it so ``models.ai.AIUploadJob`` and
``models.AIUploadJob`` resolve to the same class object (no duplicate tables).
"""
from __future__ import annotations

from _legacy.models.ai_upload import *  # noqa: F401,F403
