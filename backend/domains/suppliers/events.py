"""suppliers domain - AXIS 2 event surface (Law 3: cross-domain writes via events).

The suppliers domain owns the ``suppliers``-schema entities (supplier profile,
verification state, badges, documents, health, payouts, settlements). It publishes
events when those entities change so downstream domains (governance, orders,
logistics, comms) may react.

Transport is the sanctioned in-process ``event_bus`` (circuit-exempt data layer).
"""


from infrastructure.messaging.events.event_bus import publish

# --- notifications the suppliers domain emits after a write (downstream reacts) ---
EVENT_SUPPLIER_REGISTERED = "suppliers.supplier.registered"
EVENT_SUPPLIER_VERIFIED = "suppliers.supplier.verified"
EVENT_SUPPLIER_REJECTED = "suppliers.supplier.rejected"
EVENT_SUPPLIER_SUSPENDED = "suppliers.supplier.suspended"
EVENT_SUPPLIER_ACTIVATED = "suppliers.supplier.activated"
EVENT_SUPPLIER_BADGE_ASSIGNED = "suppliers.badge.assigned"
EVENT_SUPPLIER_BADGE_REVOKED = "suppliers.badge.revoked"
EVENT_SUPPLIER_DOCUMENT_SUBMITTED = "suppliers.document.submitted"
EVENT_SUPPLIER_DOCUMENT_REVIEWED = "suppliers.document.reviewed"
EVENT_SUPPLIER_PAYOUT_REQUESTED = "suppliers.payout.requested"
EVENT_SUPPLIER_PAYOUT_COMPLETED = "suppliers.payout.completed"
EVENT_SUPPLIER_SETTLEMENT_CREATED = "suppliers.settlement.created"
EVENT_SUPPLIER_RETURN_WINDOW_UPDATED = "suppliers.return_window.updated"


def publish_supplier_registered(supplier_id: int, user_id: int, country_code: str | None = None) -> None:
    """Emit when a new supplier registers on the platform."""
    publish(EVENT_SUPPLIER_REGISTERED, {
        "supplier_id": supplier_id,
        "user_id": user_id,
        "country_code": country_code,
    })


def publish_supplier_verified(supplier_id: int, verified_by: int, note: str | None = None) -> None:
    """Emit when an admin verifies a supplier account."""
    publish(EVENT_SUPPLIER_VERIFIED, {
        "supplier_id": supplier_id,
        "verified_by": verified_by,
        "note": note,
    })


def publish_supplier_rejected(supplier_id: int, rejected_by: int, reason: str | None = None) -> None:
    """Emit when an admin rejects a supplier verification."""
    publish(EVENT_SUPPLIER_REJECTED, {
        "supplier_id": supplier_id,
        "rejected_by": rejected_by,
        "reason": reason,
    })


def publish_supplier_suspended(supplier_id: int, suspended_by: int, reason: str | None = None) -> None:
    """Emit when a supplier account is suspended."""
    publish(EVENT_SUPPLIER_SUSPENDED, {
        "supplier_id": supplier_id,
        "suspended_by": suspended_by,
        "reason": reason,
    })


def publish_supplier_activated(supplier_id: int, activated_by: int) -> None:
    """Emit when a suspended supplier account is reactivated."""
    publish(EVENT_SUPPLIER_ACTIVATED, {
        "supplier_id": supplier_id,
        "activated_by": activated_by,
    })


def publish_supplier_badge_assigned(supplier_id: int, badge_level: str, assigned_by: int) -> None:
    """Emit when a badge tier is assigned to a supplier."""
    publish(EVENT_SUPPLIER_BADGE_ASSIGNED, {
        "supplier_id": supplier_id,
        "badge_level": badge_level,
        "assigned_by": assigned_by,
    })


def publish_supplier_badge_revoked(supplier_id: int, badge_level: str, revoked_by: int) -> None:
    """Emit when a badge tier is revoked from a supplier."""
    publish(EVENT_SUPPLIER_BADGE_REVOKED, {
        "supplier_id": supplier_id,
        "badge_level": badge_level,
        "revoked_by": revoked_by,
    })


def publish_supplier_document_submitted(supplier_id: int, document_id: int, document_type: str) -> None:
    """Emit when a supplier submits a verification document."""
    publish(EVENT_SUPPLIER_DOCUMENT_SUBMITTED, {
        "supplier_id": supplier_id,
        "document_id": document_id,
        "document_type": document_type,
    })


def publish_supplier_document_reviewed(
    supplier_id: int, document_id: int, status: str, reviewed_by: int,
) -> None:
    """Emit when an admin reviews (approves/rejects) a supplier document."""
    publish(EVENT_SUPPLIER_DOCUMENT_REVIEWED, {
        "supplier_id": supplier_id,
        "document_id": document_id,
        "status": status,
        "reviewed_by": reviewed_by,
    })


def publish_supplier_payout_requested(supplier_id: int, payout_id: int, amount: float) -> None:
    """Emit when a supplier requests a payout."""
    publish(EVENT_SUPPLIER_PAYOUT_REQUESTED, {
        "supplier_id": supplier_id,
        "payout_id": payout_id,
        "amount": amount,
    })


def publish_supplier_payout_completed(supplier_id: int, payout_id: int, amount: float) -> None:
    """Emit when a supplier payout is completed."""
    publish(EVENT_SUPPLIER_PAYOUT_COMPLETED, {
        "supplier_id": supplier_id,
        "payout_id": payout_id,
        "amount": amount,
    })


def publish_supplier_settlement_created(supplier_id: int, settlement_id: int, order_id: int) -> None:
    """Emit when a settlement record is created for a supplier order."""
    publish(EVENT_SUPPLIER_SETTLEMENT_CREATED, {
        "supplier_id": supplier_id,
        "settlement_id": settlement_id,
        "order_id": order_id,
    })


def publish_supplier_return_window_updated(supplier_id: int, return_window_days: int) -> None:
    """Emit when a supplier's return window configuration changes."""
    publish(EVENT_SUPPLIER_RETURN_WINDOW_UPDATED, {
        "supplier_id": supplier_id,
        "return_window_days": return_window_days,
    })


__all__ = [
    "EVENT_SUPPLIER_REGISTERED",
    "EVENT_SUPPLIER_VERIFIED",
    "EVENT_SUPPLIER_REJECTED",
    "EVENT_SUPPLIER_SUSPENDED",
    "EVENT_SUPPLIER_ACTIVATED",
    "EVENT_SUPPLIER_BADGE_ASSIGNED",
    "EVENT_SUPPLIER_BADGE_REVOKED",
    "EVENT_SUPPLIER_DOCUMENT_SUBMITTED",
    "EVENT_SUPPLIER_DOCUMENT_REVIEWED",
    "EVENT_SUPPLIER_PAYOUT_REQUESTED",
    "EVENT_SUPPLIER_PAYOUT_COMPLETED",
    "EVENT_SUPPLIER_SETTLEMENT_CREATED",
    "EVENT_SUPPLIER_RETURN_WINDOW_UPDATED",
    "publish_supplier_registered",
    "publish_supplier_verified",
    "publish_supplier_rejected",
    "publish_supplier_suspended",
    "publish_supplier_activated",
    "publish_supplier_badge_assigned",
    "publish_supplier_badge_revoked",
    "publish_supplier_document_submitted",
    "publish_supplier_document_reviewed",
    "publish_supplier_payout_requested",
    "publish_supplier_payout_completed",
    "publish_supplier_settlement_created",
    "publish_supplier_return_window_updated",
]

# imports merged from services/
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

# base classes merged from services/
class SuppliersEvent:
    """Base class for all suppliers-domain events."""

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

# derived classes merged from services/
class SupplierRegistered(SuppliersEvent):
    supplier_id: int = 0
    user_id: Optional[int] = None
    company_name: str = ""
    country_code: str = ""
    event_type: str = field(default=EVENT_SUPPLIER_REGISTERED, init=False)
class SupplierSuspended(SuppliersEvent):
    supplier_id: int = 0
    reason: str = ""
    suspended_by: Optional[int] = None
    event_type: str = field(default=EVENT_SUPPLIER_SUSPENDED, init=False)
class SupplierVerified(SuppliersEvent):
    supplier_id: int = 0
    verified_by: Optional[int] = None
    event_type: str = field(default=EVENT_SUPPLIER_VERIFIED, init=False)
