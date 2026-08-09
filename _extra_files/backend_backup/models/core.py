"""Re-export of the canonical core models.

The ``models.comms`` package is the canonical home for these ORM classes.
This flat module now forwards to it so that ``models.Address`` and
``models.comms.core.Address`` resolve to the *same* class object, eliminating
the duplicate-table collision flagged by the architecture audit.
"""
from __future__ import annotations

from models.comms.core import *  # noqa: F401,F403
