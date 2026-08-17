"""``models.identity`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat module ``models/user.py`` (preserved for backward compatibility); this
package forwards to it so ``models.identity.User`` and ``models.User`` resolve
to the same class object (no duplicate tables).
"""
from __future__ import annotations

from models.user import *  # noqa: F401,F403
