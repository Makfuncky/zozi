"""suppliers domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.suppliers.models`` or ``domains.suppliers.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session


# This domain currently exposes no ORM models under domains.suppliers.models/.
# Add read helpers here as models are introduced.


# --- COMMS-IMPORT: sanctioned model/utils surface consumed by comms (Law 3) ---
from domains.suppliers.models.suppliers import *
from domains.suppliers.models.suppliers import __all__
