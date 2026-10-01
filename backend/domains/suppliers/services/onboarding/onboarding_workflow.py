"""Supplier onboarding workflow service — state machine for supplier onboarding."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.suppliers.models.suppliers import SupplierProfile
from domains.suppliers.models.supplier_country_sync import SupplierOnboardingSync

logger = logging.getLogger(__name__)

# Valid onboarding workflow states
STATE_NOT_STARTED = "not_started"
STATE_PROFILE_CREATED = "profile_created"
STATE_DOCUMENTS_SUBMITTED = "documents_submitted"
STATE_KYC_PENDING = "kyc_pending"
STATE_KYC_APPROVED = "kyc_approved"
STATE_KYC_REJECTED = "kyc_rejected"
STATE_CONTRACT_PENDING = "contract_pending"
STATE_CONTRACT_SIGNED = "contract_signed"
STATE_ACTIVE = "active"
STATE_SUSPENDED = "suspended"

# Allowed state transitions: current_state -> [allowed_next_states]
VALID_TRANSITIONS: dict[str, list[str]] = {
    STATE_NOT_STARTED: [STATE_PROFILE_CREATED, STATE_SUSPENDED],
    STATE_PROFILE_CREATED: [STATE_DOCUMENTS_SUBMITTED, STATE_SUSPENDED],
    STATE_DOCUMENTS_SUBMITTED: [STATE_KYC_PENDING, STATE_SUSPENDED],
    STATE_KYC_PENDING: [STATE_KYC_APPROVED, STATE_KYC_REJECTED, STATE_SUSPENDED],
    STATE_KYC_APPROVED: [STATE_CONTRACT_PENDING, STATE_SUSPENDED],
    STATE_KYC_REJECTED: [STATE_DOCUMENTS_SUBMITTED, STATE_SUSPENDED],
    STATE_CONTRACT_PENDING: [STATE_CONTRACT_SIGNED, STATE_SUSPENDED],
    STATE_CONTRACT_SIGNED: [STATE_ACTIVE, STATE_SUSPENDED],
    STATE_ACTIVE: [STATE_SUSPENDED],
    STATE_SUSPENDED: [STATE_ACTIVE, STATE_NOT_STARTED],
}


def get_workflow_state(supplier_id: int, db: Session) -> dict[str, Any]:
    """Return the current onboarding workflow state for a supplier."""
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    now = datetime.now(timezone.utc)

    sync = db.query(SupplierOnboardingSync).filter(
        SupplierOnboardingSync.supplier_id == supplier_id,
    ).order_by(SupplierOnboardingSync.id.desc()).first()

    if sync:
        current_state = sync.kyc_status or STATE_NOT_STARTED
    elif supplier.is_verified:
        current_state = STATE_ACTIVE
    elif supplier.verification_status == "verified":
        current_state = STATE_ACTIVE
    else:
        current_state = STATE_NOT_STARTED

    allowed_transitions = VALID_TRANSITIONS.get(current_state, [])

    return {
        "supplier_id": supplier_id,
        "current_state": current_state,
        "allowed_transitions": allowed_transitions,
        "is_terminal": current_state in (STATE_ACTIVE, STATE_SUSPENDED),
        "checked_at": now.isoformat(),
    }


def transition_state(
    supplier_id: int,
    new_state: str,
    db: Session,
) -> dict[str, Any]:
    """Transition the supplier's onboarding workflow to a new state.

    Validates the transition against the allowed state machine and
    updates the onboarding sync record.
    """
    supplier = db.query(SupplierProfile).filter(SupplierProfile.id == supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier profile not found")

    if new_state not in VALID_TRANSITIONS and new_state not in (
        STATE_NOT_STARTED, STATE_PROFILE_CREATED, STATE_DOCUMENTS_SUBMITTED,
        STATE_KYC_PENDING, STATE_KYC_APPROVED, STATE_KYC_REJECTED,
        STATE_CONTRACT_PENDING, STATE_CONTRACT_SIGNED, STATE_ACTIVE, STATE_SUSPENDED,
    ):
        raise HTTPException(status_code=400, detail=f"Unknown workflow state: {new_state}")

    now = datetime.now(timezone.utc)

    sync = db.query(SupplierOnboardingSync).filter(
        SupplierOnboardingSync.supplier_id == supplier_id,
    ).order_by(SupplierOnboardingSync.id.desc()).first()

    current_state = sync.kyc_status if sync else STATE_NOT_STARTED

    allowed = VALID_TRANSITIONS.get(current_state, [])
    if new_state not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition from '{current_state}' to '{new_state}'. Allowed: {allowed}",
        )

    if sync:
        sync.kyc_status = new_state
        db.commit()
        db.refresh(sync)
    else:
        sync = SupplierOnboardingSync(
            supplier_id=supplier_id,
            pipeline_type="onboarding",
            kyc_status=new_state,
        )
        db.add(sync)
        db.commit()
        db.refresh(sync)

    new_allowed = VALID_TRANSITIONS.get(new_state, [])

    return {
        "supplier_id": supplier_id,
        "previous_state": current_state,
        "current_state": new_state,
        "allowed_transitions": new_allowed,
        "transitioned_at": now.isoformat(),
    }
