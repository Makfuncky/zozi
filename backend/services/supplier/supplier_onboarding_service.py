"""
Supplier Onboarding Service
Renders dynamic document upload fields from supplier_requirements_json.
"""
import json
import logging
from typing import Dict, Any, List, Optional

from db.database import get_db_context
from models import CountryConfig, SupplierOnboardingSync

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
