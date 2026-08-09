"""Re-export of the canonical supplier models.

The ``models.comms`` package is the canonical home for these ORM classes.
This flat module now forwards to it so that ``models.SupplierProfile`` and
``models.comms.suppliers.SupplierProfile`` resolve to the *same* class object,
eliminating the duplicate-table collision flagged by the architecture audit.
"""
from __future__ import annotations

from models.comms.suppliers import *  # noqa: F401,F403
