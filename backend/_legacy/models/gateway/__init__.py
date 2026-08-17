"""``models.gateway`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat module ``models/payments.py`` (preserved for backward compatibility);
this package forwards to it so ``models.gateway.Payment`` and
``models.Payment`` resolve to the same class object (no duplicate tables).
"""
from __future__ import annotations

from _legacy.models.payments import *  # noqa: F401,F403
