"""HR domain — typed cross-domain events (Law 3).

Cross-domain **writes** travel exclusively through ``events.py`` /
``subscribers.py``. Each event is a frozen dataclass with an event-type
discriminator, a UTC ``occurred_at`` timestamp, and a ``serialize()``
method so the event bus can emit them to subscribers.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Canonical event type constants (shared contract)
EVENT_EMPLOYEE_ONBOARDED = "hr.employee.onboarded"
EVENT_EMPLOYEE_OFFBOARDED = "hr.employee.offboarded"
EVENT_LEAVE_REQUESTED = "hr.leave.requested"
EVENT_PAYROLL_PROCESSED = "hr.payroll.processed"

# ── base ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class HREvent:
    """Base class for all hr-domain events."""

    event_type: str = field(init=False)
    event_id: str = field(default_factory=lambda: str(uuid4()), init=False)
    occurred_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc), init=False
    )

    def serialize(self) -> Dict[str, Any]:
        """Plain-dict form for the event bus."""
        d = asdict(self)
        d["occurred_at"] = self.occurred_at.isoformat()
        return d

# ── onboarding events ────────────────────────────────────────────────────

@dataclass(frozen=True)
class EmployeeOnboarded(HREvent):
    employee_id: int = 0
    user_id: Optional[int] = None
    country_code: str = ""
    department: str = ""
    event_type: str = field(default=EVENT_EMPLOYEE_ONBOARDED, init=False)

# ── offboarding events ────────────────────────────────────────────────────

@dataclass(frozen=True)
class EmployeeOffboarded(HREvent):
    employee_id: int = 0
    user_id: Optional[int] = None
    reason: str = ""
    event_type: str = field(default=EVENT_EMPLOYEE_OFFBOARDED, init=False)

# ── leave events ──────────────────────────────────────────────────────────

@dataclass(frozen=True)
class LeaveRequested(HREvent):
    request_id: int = 0
    employee_id: int = 0
    leave_type: str = ""
    start_date: str = ""
    end_date: str = ""
    event_type: str = field(default=EVENT_LEAVE_REQUESTED, init=False)

# ── payroll events ────────────────────────────────────────────────────────

@dataclass(frozen=True)
class PayrollProcessed(HREvent):
    payroll_id: int = 0
    employee_id: int = 0
    period_start: str = ""
    period_end: str = ""
    amount: str = ""
    event_type: str = field(default=EVENT_PAYROLL_PROCESSED, init=False)

# ── publish helpers (integrate with canonical event bus) ──────────────────

def publish_employee_onboarded(employee_id: int, country_code: str, department: str, user_id: Optional[int] = None) -> None:
    """Publish an EmployeeOnboarded event to the canonical event bus."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = EmployeeOnboarded(employee_id=employee_id, user_id=user_id, country_code=country_code, department=department)
        publish(EVENT_EMPLOYEE_ONBOARDED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish EmployeeOnboarded event: %s", exc)

def publish_employee_offboarded(employee_id: int, reason: str, user_id: Optional[int] = None) -> None:
    """Publish an EmployeeOffboarded event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = EmployeeOffboarded(employee_id=employee_id, user_id=user_id, reason=reason)
        publish(EVENT_EMPLOYEE_OFFBOARDED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish EmployeeOffboarded event: %s", exc)

def publish_leave_requested(request_id: int, employee_id: int, leave_type: str, start_date: str, end_date: str) -> None:
    """Publish a LeaveRequested event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = LeaveRequested(request_id=request_id, employee_id=employee_id, leave_type=leave_type, start_date=start_date, end_date=end_date)
        publish(EVENT_LEAVE_REQUESTED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish LeaveRequested event: %s", exc)

def publish_payroll_processed(payroll_id: int, employee_id: int, period_start: str, period_end: str, amount: str) -> None:
    """Publish a PayrollProcessed event."""
    try:
        from infrastructure.messaging.events.event_bus import publish
        event = PayrollProcessed(payroll_id=payroll_id, employee_id=employee_id, period_start=period_start, period_end=period_end, amount=amount)
        publish(EVENT_PAYROLL_PROCESSED, event.serialize())
    except Exception as exc:
        logger.warning("Failed to publish PayrollProcessed event: %s", exc)

__all__ = [
    # Event type constants
    "EVENT_EMPLOYEE_ONBOARDED",
    "EVENT_EMPLOYEE_OFFBOARDED",
    "EVENT_LEAVE_REQUESTED",
    "EVENT_PAYROLL_PROCESSED",
    # Event classes
    "HREvent",
    "EmployeeOnboarded",
    "EmployeeOffboarded",
    "LeaveRequested",
    "PayrollProcessed",
    # Publish helpers
    "publish_employee_onboarded",
    "publish_employee_offboarded",
    "publish_leave_requested",
    "publish_payroll_processed",
]
