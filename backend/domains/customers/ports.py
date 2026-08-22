"""customers domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these functions instead
of importing ``domains.customers.models`` or ``domains.customers.services`` directly.

These are pure read helpers: no writes, no business decisions, no permission
checks (callers remain responsible for feature gating via ``rbac``).
"""

from __future__ import annotations

from typing import List, Optional

from sqlalchemy.orm import Session

# A3 / RESOLVER §26 ACC-01 — re-export the customer-schema ORM classes the
# accounts god-module hub used to own, so cross-domain readers resolve them via
# this sanctioned ports surface (Law 3) instead of ``domains.accounts.models``.
from domains.customers.models.customer_schema_models import Cart, Referral

