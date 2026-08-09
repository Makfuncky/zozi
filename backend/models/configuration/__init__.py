"""``models.configuration`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for these cross-cutting concerns
still live in their flat modules (``models/admin.py``, ``models/mixins.py``,
``models/onboarding.py``, ``models/country_control.py``), preserved for
backward compatibility; this package forwards to them so the flat and
domain-qualified imports resolve to the same class objects (no duplicate
tables).
"""
from __future__ import annotations

from models.admin import *  # noqa: F401,F403
from models.mixins import *  # noqa: F401,F403
from models.onboarding import *  # noqa: F401,F403
from models.country_control import *  # noqa: F401,F403
