"""Employee activity logger — append-only audit trail for HR domain actions.

Writes to the employee_activity_logs table. Supports both positional calling
(convenience for simple events) and keyword calling (full audit context).
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def log_activity(
    db,
    actor_employee_id: int,
    action: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    *,
    country_code: Optional[str] = None,
    metadata_json: Optional[dict] = None,
    target_employee_id: Optional[int] = None,
) -> None:
    """Write an entry to the employee_activity_logs table.

    Can be called positionally for simple events::

        log_activity(db, emp.id, "profile_updated", "employee_profile", str(emp.id))

    Or with keyword args for full audit context::

        log_activity(db=db, actor_employee_id=x, action=y, entity_type=z,
                     entity_id=str(eid), country_code=cc, metadata_json={...})
    """
    try:
        from domains.hr.models.employee_models import EmployeeActivityLog

        # Merge target_employee_id into metadata if provided (no dedicated column)
        merged_meta = metadata_json or {}
        if target_employee_id is not None:
            merged_meta = {**merged_meta, "target_employee_id": target_employee_id}

        log_entry = EmployeeActivityLog(
            actor_employee_id=actor_employee_id,
            action=action,
            entity_type=entity_type,
            entity_id=int(entity_id) if entity_id is not None else None,
            country_code=country_code,
            metadata_json=merged_meta or None,
        )
        db.add(log_entry)
        db.commit()
    except Exception as exc:
        logger.debug("Activity log write failed (non-critical): %s", exc)
