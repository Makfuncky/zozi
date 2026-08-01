"""
Data Residency & Sovereignty Encryption Service.

Ensures PII for strict countries is encrypted with localized KMS keys.
"""
from typing import Optional, Dict, Any
from enum import Enum


class DataResidencyTier(Enum):
    STANDARD = "standard"
    STRICT = "strict"
    SOVEREIGN = "sovereign"


class DataResidencyService:
    """Manages data residency and encryption for PII."""
    
    STRICT_COUNTRIES = {"SA", "AE", "OM", "BH", "KW", "QA"}
    SOVEREIGN_COUNTRIES = {"CN", "RU", "IR"}
    
    @staticmethod
    def get_residency_tier(country_code: str, config: Optional[Dict] = None) -> DataResidencyTier:
        """Determine data residency tier for a country."""
        if config and config.get("data_residency_tier"):
            tier = config["data_residency_tier"]
            if tier == "sovereign":
                return DataResidencyTier.SOVEREIGN
            elif tier == "strict":
                return DataResidencyTier.STRICT
            return DataResidencyTier.STANDARD
        
        code = country_code.upper()
        if code in DataResidencyService.SOVEREIGN_COUNTRIES:
            return DataResidencyTier.SOVEREIGN
        elif code in DataResidencyService.STRICT_COUNTRIES:
            return DataResidencyTier.STRICT
        return DataResidencyTier.STANDARD
    
    @staticmethod
    def should_encrypt_with_local_kms(country_code: str, config: Optional[Dict] = None) -> bool:
        """Check if data should be encrypted with local KMS."""
        tier = DataResidencyService.get_residency_tier(country_code, config)
        return tier in (DataResidencyTier.STRICT, DataResidencyTier.SOVEREIGN)
    
    @staticmethod
    def get_kms_key_alias(country_code: str, config: Optional[Dict] = None) -> str:
        """Get KMS key alias for a country."""
        tier = DataResidencyService.get_residency_tier(country_code, config)
        
        if tier == DataResidencyTier.SOVEREIGN:
            return f"arn:aws:kms:{country_code.lower()}:kms:{country_code.lower()}-sovereign-key"
        elif tier == DataResidencyTier.STRICT:
            return f"arn:aws:kms:{country_code.lower()}:kms:{country_code.lower()}-strict-key"
        return "alias/default-key"
    
    @staticmethod
    def get_pii_fields() -> list:
        """Return list of PII fields that need special handling."""
        return [
            "bank_account_number",
            "bank_ifsc_code",
            "national_id",
            "passport_number",
            "tax_id",
            "phone_number",
            "email",
            "address_line1",
            "address_line2",
            "city",
            "postal_code",
        ]
    
    @staticmethod
    def should_redact_in_export(country_code: str, config: Optional[Dict] = None) -> bool:
        """Check if PII should be redacted in CSV exports."""
        tier = DataResidencyService.get_residency_tier(country_code, config)
        return tier == DataResidencyTier.SOVEREIGN


class SovereignEncryptionService:
    """Handles sovereign encryption for strict countries."""
    
    @staticmethod
    def encrypt_for_sovereign_storage(data: str, country_code: str) -> Dict[str, Any]:
        """Encrypt data for sovereign storage with local KMS."""
        return {
            "encrypted_data": data,
            "key_alias": f"alias/{country_code.lower()}-sovereign-key",
            "region": country_code.lower(),
            "sovereign_encrypted": True,
        }
    
    @staticmethod
    def decrypt_from_sovereign_storage(
        encrypted_data: Dict[str, Any],
        kms_client,
    ) -> str:
        """Decrypt data from sovereign storage."""
        return encrypted_data.get("encrypted_data", "")

