"""
Supplier Onboarding Service
Renders dynamic document upload fields from supplier_requirements_json.

Also owns the DB work for the onboarding pipeline endpoints that previously
lived in ``routers/supplier/onboarding.py`` so that router stays a thin
delegator (layering: LC1/W1).
"""
import json
import logging
from typing import Dict, Any, List, Optional

from fastapi import HTTPException

from data.db import get_db_context
from data.models import CountryConfig, SupplierOnboardingSync, User
from services.supplier.onboarding_pipeline import get_onboarding_service

logger = logging.getLogger(__name__)


class SupplierOnboardingService:
    """Manages supplier onboarding requirements per country."""

    @staticmethod
    def get_required_documents(country_code: str) -> Dict[str, Any]:
        """Get required documents for supplier onboarding in a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()

            if not config or not config.supplier_requirements_json:
                return {
                    "kyc_level": "standard",
                    "required_documents": [],
                    "document_fields": []
                }

            try:
                requirements = json.loads(config.supplier_requirements_json) if isinstance(config.supplier_requirements_json, str) else config.supplier_requirements_json
            except (json.JSONDecodeError, TypeError):
                return {
                    "kyc_level": "standard",
                    "required_documents": [],
                    "document_fields": []
                }

            return requirements

    @staticmethod
    def get_document_fields(country_code: str) -> List[Dict[str, Any]]:
        """Get dynamic document upload fields for a country."""
        requirements = SupplierOnboardingService.get_required_documents(country_code)

        base_fields = [
            {
                "name": "business_license",
                "label": "Business License",
                "type": "file",
                "required": True,
                "mime_types": ["application/pdf", "image/jpeg", "image/png"],
                "max_size_mb": 10
            },
            {
                "name": "tax_registration",
                "label": "Tax Registration Document",
                "type": "file",
                "required": True,
                "mime_types": ["application/pdf"],
                "max_size_mb": 10
            }
        ]

        custom_docs = requirements.get("required_documents", [])
        for doc in custom_docs:
            base_fields.append({
                "name": doc.get("field_name", doc.get("id", "custom_document")),
                "label": doc.get("label", "Additional Document"),
                "type": "file",
                "required": doc.get("required", False),
                "mime_types": doc.get("mime_types", ["application/pdf", "image/jpeg", "image/png"]),
                "max_size_mb": doc.get("max_size_mb", 10)
            })

        return base_fields

    @staticmethod
    def get_kyc_level(country_code: str) -> str:
        """Get KYC level for a country."""
        requirements = SupplierOnboardingService.get_required_documents(country_code)
        return requirements.get("kyc_level", "standard")

    @staticmethod
    def get_onboarding_fee(country_code: str) -> Optional[float]:
        """Get onboarding fee for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()

            if config and config.supplier_onboarding_fee:
                return float(config.supplier_onboarding_fee)
        return None

    @staticmethod
    def get_monthly_fee(country_code: str) -> Optional[float]:
        """Get monthly fee for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()

            if config and config.supplier_monthly_fee:
                return float(config.supplier_monthly_fee)
        return None

    @staticmethod
    def get_rating_threshold(country_code: str) -> Optional[float]:
        """Get minimum supplier rating threshold for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()

            if config and config.supplier_rating_threshold:
                return float(config.supplier_rating_threshold)
        return None

    @staticmethod
    def check_supplier_eligibility(country_code: str, supplier_id: int) -> Dict[str, Any]:
        """Check if a supplier is eligible for a country based on requirements."""
        with get_db_context() as db:
            sync = db.query(SupplierOnboardingSync).filter(
                SupplierOnboardingSync.country_code == country_code.upper(),
                SupplierOnboardingSync.supplier_id == supplier_id
            ).first()

            if not sync:
                return {
                    "eligible": False,
                    "reason": "No onboarding sync found",
                    "kyc_status": "pending"
                }

            return {
                "eligible": sync.kyc_status == "approved",
                "reason": sync.notes or "",
                "kyc_status": sync.kyc_status
            }


# ---------------------------------------------------------------------------
# Onboarding pipeline DB helpers (moved out of routers/supplier/onboarding.py)
# ---------------------------------------------------------------------------


def _get_user_or_404(current_user: dict) -> User:
    """Resolve the authenticated user from the JWT claims (404 if absent)."""
    with get_db_context() as db:
        user = db.query(User).filter(User.id == int(current_user["sub"])).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user


def create_onboarding_pipeline(
    current_user: dict,
    pipeline_type: str = "kyc",
) -> Dict[str, Any]:
    """Create a new onboarding pipeline for the authenticated user."""
    user = _get_user_or_404(current_user)

    with get_db_context() as db:
        service = get_onboarding_service(db)
        pipeline = service.create_pipeline(user.id, pipeline_type)

        return {
            "pipeline_id": pipeline.id,
            "type": pipeline.pipeline_type,
            "status": pipeline.status
        }


def process_pipeline_document(
    pipeline_id: int,
    document_type: str,
    content: bytes,
) -> Dict[str, Any]:
    """Run an uploaded document through OCR/verification for a pipeline."""
    with get_db_context() as db:
        service = get_onboarding_service(db)
        verification = service.process_document(pipeline_id, document_type, content)

        return {
            "verification_id": verification.id,
            "document_type": verification.document_type,
            "status": verification.status,
            "ocr_confidence": verification.ocr_result.confidence_score if verification.ocr_result else None
        }


def create_kyc_verification_record(
    current_user: dict,
    documents: List[dict],
) -> Dict[str, Any]:
    """Create a KYC verification record for the authenticated user."""
    user = _get_user_or_404(current_user)

    with get_db_context() as db:
        service = get_onboarding_service(db)
        kyc = service.create_kyc_verification(user.id, documents)

        return {
            "kyc_id": kyc.id,
            "status": kyc.status,
            "document_types": kyc.document_types
        }


def get_onboarding_status_for_user(current_user: dict) -> Dict[str, Any]:
    """Return the latest onboarding pipeline status for the authenticated user."""
    user = _get_user_or_404(current_user)

    with get_db_context() as db:
        service = get_onboarding_service(db)
        status = service.get_pipeline_status(user.id)

        if not status:
            return {"status": "not_started"}

        return status


def complete_pipeline_step(pipeline_id: int, step_name: str) -> Dict[str, Any]:
    """Mark an onboarding pipeline step as completed."""
    with get_db_context() as db:
        service = get_onboarding_service(db)
        step = service.complete_step(pipeline_id, step_name)

        return {
            "step": step.step_name,
            "status": step.status,
            "completed_at": step.completed_at.isoformat() if step.completed_at else None
        }
