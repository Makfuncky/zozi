"""security domain - sanctioned cross-domain READ surface (ports).

Per NEW_STRUCTURE.md Law 3, cross-domain *reads* may ONLY happen through a
publishing domain's ``ports.py``. Other domains import these classes instead
of importing ``domains.security.models`` directly.

A3 / RESOLVER §26 ACC-01 — re-export the security-schema ORM classes the
accounts god-module hub used to own, so cross-domain readers resolve them via
this sanctioned ports surface (Law 3) instead of ``domains.governance.models``.
"""

from __future__ import annotations

from domains.security.models.security_schema_models import (
    AlertEscalationRule,
    DocumentVerification,
    KYCVerification,
)
