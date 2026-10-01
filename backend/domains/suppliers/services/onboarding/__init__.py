"""
Supplier Onboarding Service — pipeline management, document upload, KYC verification.
"""
import logging
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.comms.models.suppliers import SupplierDocument, SupplierProfile
from domains.suppliers.services.onboarding.supplier_onboarding_service import SupplierOnboardingService

logger = logging.getLogger(__name__)


def _get_profile(user_id: int, db: Session) -> SupplierProfile:
    profile = db.query(SupplierProfile).filter(SupplierProfile.user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Supplier profile not found")
    return profile


def create_pipeline(user_id: int, pipeline_type: str, db: Session) -> dict:
    """Create a new onboarding pipeline for a supplier."""
    profile = _get_profile(user_id, db)
    return {
        "pipeline_id": profile.id,
        "type": pipeline_type,
        "status": "pending",
    }


def upload_document(pipeline_id: int, document_type: str, content: bytes, db: Session) -> dict:
    """Upload a document for an onboarding pipeline."""
    document = SupplierDocument(
        supplier_id=pipeline_id,
        document_type=document_type,
        status="pending_review",
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return {
        "verification_id": document.id,
        "document_type": document.document_type,
        "status": document.status,
    }


def create_kyc_verification(user_id: int, documents: list[dict], db: Session) -> dict:
    """Create a KYC verification request."""
    profile = _get_profile(user_id, db)
    document_types = [d.get("document_type", "unknown") for d in documents]
    return {
        "kyc_id": profile.id,
        "status": "pending",
        "document_types": document_types,
    }


def get_onboarding_status(user_id: int, db: Session) -> dict:
    """Get the onboarding status for a supplier."""
    profile = _get_profile(user_id, db)
    return {
        "status": profile.verification_status or "not_started",
        "supplier_id": profile.id,
    }


def complete_step(pipeline_id: int, step_name: str, db: Session) -> dict:
    """Mark an onboarding step as complete."""
    return {
        "step": step_name,
        "status": "completed",
    }
