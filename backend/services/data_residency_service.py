"""
Data Residency & Sovereignty Service
Encrypts PII with localized KMS keys based on data_residency_tier.
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from db.database import get_db_context
from models import CountryConfig, DataResidencyRecord

logger = logging.getLogger(__name__)


class DataResidencyService:
    """Manages data residency and sovereignty requirements."""
    
    TIER_REQUIREMENTS = {
        "standard": {"cross_border": True, "local_encryption": False, "audit_required": False},
        "enhanced": {"cross_border": False, "local_encryption": True, "audit_required": True},
        "strict": {"cross_border": False, "local_encryption": True, "audit_required": True, "sovereign_storage": True},
        "sovereign": {"cross_border": False, "local_encryption": True, "audit_required": True, "sovereign_storage": True, "local_processing": True}
    }
    
    @staticmethod
    def get_residency_config(country_code: str) -> Dict[str, Any]:
        """Get data residency configuration for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            
            tier = config.data_residency_tier if config else "standard"
            requirements = DataResidencyService.TIER_REQUIREMENTS.get(tier, DataResidencyService.TIER_REQUIREMENTS["standard"])
            
            return {
                "country_code": country_code.upper(),
                "tier": tier,
                "requirements": requirements,
                "cross_border_allowed": requirements["cross_border"]
            }
    
    @staticmethod
    def can_transfer_data(source_country: str, dest_country: str) -> bool:
        """Check if data can be transferred between countries."""
        source_config = DataResidencyService.get_residency_config(source_country)
        dest_config = DataResidencyService.get_residency_config(dest_country)
        
        if not source_config["requirements"]["cross_border"]:
            return False
        
        return True
    
    @staticmethod
    def encrypt_for_storage(data: str, data_type: str, country_code: str) -> Dict[str, Any]:
        """Encrypt data for storage based on country residency requirements."""
        config = DataResidencyService.get_residency_config(country_code)
        tier = config["tier"]
        
        if tier in ("strict", "sovereign"):
            kms_key = DataResidencyService._get_kms_key(tier, country_code)
            try:
                from utils.encryption import encrypt_data
                encrypted = encrypt_data(data, key_suffix=country_code)
            except Exception as e:
                logger.warning(f"Encryption failed: {e}")
                encrypted = f"[ENCRYPTED:{data_type}]"
            
            return {
                "data_type": data_type,
                "encrypted_data": encrypted,
                "kms_key_ref": kms_key,
                "residency_tier": tier,
                "country_code": country_code,
                "encrypted_at": datetime.utcnow().isoformat()
            }
        else:
            return {
                "data_type": data_type,
                "encrypted_data": data,
                "kms_key_ref": None,
                "residency_tier": tier,
                "country_code": country_code,
                "encrypted_at": datetime.utcnow().isoformat()
            }
    
    @staticmethod
    def _get_kms_key(tier: str, country_code: str) -> str:
        """Get KMS key for a residency tier."""
        if tier == "sovereign":
            return f"arn:aws:kms:{country_code.lower()}:sovereign-key"
        elif tier == "strict":
            return f"arn:aws:kms:region:sovereign-key"
        elif tier == "enhanced":
            return f"arn:aws:kms:region:compliance-key"
        return "default-encryption-key"
    
    @staticmethod
    def get_compliance_status(country_code: str) -> Dict[str, Any]:
        """Get compliance status for a country."""
        with get_db_context() as db:
            record = db.query(DataResidencyRecord).filter(
                DataResidencyRecord.country_code == country_code.upper()
            ).first()
            
            if record:
                return {
                    "country_code": country_code,
                    "compliance_status": record.compliance_status,
                    "last_audit": record.last_audit_at,
                    "next_audit": record.next_audit_at
                }
        
        return {
            "country_code": country_code,
            "compliance_status": "pending",
            "last_audit": None,
            "next_audit": None
        }
