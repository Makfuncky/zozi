"""``models.security`` domain package (re-export facade).

Per the AI File Placement Contract, ``backend/models/`` is organised as
domain folders. The canonical ORM classes for this domain still live in the
flat modules ``models/fraud.py`` and ``models/incident.py`` (preserved for
backward compatibility); this package forwards to them so
``models.security.FraudEvent`` / ``models.security.IncidentWarRoom`` and the
flat ``models.FraudEvent`` / ``models.IncidentWarRoom`` resolve to the same
class objects (no duplicate tables).
"""
from __future__ import annotations

from models.fraud import *  # noqa: F401,F403
from models.incident import *  # noqa: F401,F403
