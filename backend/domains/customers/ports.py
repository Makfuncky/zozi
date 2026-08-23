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
# this sanctioned ports surface (Law 3) instead of ``domains.governance.models``.
from domains.governance.models.core import Cart
from domains.governance.models.user import Referral
from infrastructure.utils.export_read_service import db_product_all_2, db_order_all_1, db_auditlog_query_4, MAX_EXPORT_ROWS, db_coupon_all_3, db_user_all_0
