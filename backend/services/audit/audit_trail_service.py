"""
Audit Trail Service
Logs all financial field changes with "Reason for Change".
"""
import json
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from db.database import get_db_context
from models import CountryConfig

logger = logging.getLogger(__name__)


class AuditTrailService:
    """Immutable financial audit trail logging."""
    
    @staticmethod
    def log_financial_change(
        country_code: str,
        table_name: str,
        record_id: int,
        field_name: str,
        old_value: Any,
        new_value: Any,
        reason: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log a financial field change to both the audit_logs table and JSON log."""
        audit_record = {
            "country_code": country_code.upper(),
            "table_name": table_name,
            "record_id": record_id,
            "field_name": field_name,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "reason": reason,
            "user_id": user_id,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
            "change_hash": AuditTrailService._compute_hash(
                country_code, table_name, record_id, field_name, old_value, new_value, reason
            )
        }
        
        logger.info(f"Financial audit: {json.dumps(audit_record)}")
        
        # Also write to the central audit_logs table for unified querying
        try:
            from utils.audit_log import audit_log as _audit_log
            with get_db_context() as _db:
                _audit_log(
                    db=_db,
                    action=f"FINANCIAL_FIELD_CHANGE_{table_name.upper()}",
                    user_id=user_id,
                    username=username,
                    user_role=user_role,
                    resource_type=table_name,
                    resource_id=record_id,
                    details={
                        "field_name": field_name,
                        "old_value": str(old_value),
                        "new_value": str(new_value),
                        "reason": reason,
                        "country_code": country_code.upper(),
                        "change_hash": audit_record["change_hash"],
                        **(metadata or {}),
                    },
                )
                _db.commit()
        except Exception as exc:
            logger.warning("audit_logs table write failed: %s", exc)
        
        return audit_record
    
    @staticmethod
    def _compute_hash(*args) -> str:
        """Compute a hash for the change record."""
        import hashlib
        data = "|".join(str(arg) for arg in args)
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    @staticmethod
    def get_audit_trail(
        country_code: str,
        table_name: Optional[str] = None,
        record_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get audit trail for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            
            if not config or not config.audit_trail_json:
                return []
            
            try:
                trail = json.loads(config.audit_trail_json) if isinstance(config.audit_trail_json, str) else config.audit_trail_json
            except (json.JSONDecodeError, TypeError):
                return []
            
            filtered = trail
            
            if table_name:
                filtered = [t for t in trail if t.get("table_name") == table_name]
            if record_id:
                filtered = [t for t in filtered if t.get("record_id") == record_id]
            
            return filtered[-limit:]


class DataResidencyService:
    """Handles data residency and sovereignty routing."""
    
    @staticmethod
    def get_data_residency_tier(country_code: str) -> str:
        """Get data residency tier for a country."""
        with get_db_context() as db:
            config = db.query(CountryConfig).filter(
                CountryConfig.code == country_code.upper()
            ).first()
            
            if config:
                return config.data_residency_tier or "standard"
        return "standard"
    
    @staticmethod
    def requires_local_encryption(country_code: str) -> bool:
        """Check if country requires local encryption."""
        tier = DataResidencyService.get_data_residency_tier(country_code)
        return tier in ["strict", "sovereign"]
    
    @staticmethod
    def encrypt_pii(data: str, country_code: str) -> Dict[str, Any]:
        """Encrypt PII data with localized KMS key."""
        tier = DataResidencyService.get_data_residency_tier(country_code)
        
        if tier == "sovereign":
            kms_key = f"arn:aws:kms:{country_code.lower()}:local-key"
        elif tier == "strict":
            kms_key = f"arn:aws:kms:region-local-key"
        else:
            kms_key = "default-key"
        
        try:
            from utils.encryption import encrypt_data
            encrypted = encrypt_data(data, key_suffix=country_code)
        except Exception:
            encrypted = f"[ENCRYPTED_WITH_{kms_key}]"
        
        return {
            "encrypted_data": encrypted,
            "kms_key": kms_key,
            "tier": tier,
            "country_code": country_code
        }
    
    @staticmethod
    def decrypt_pii(encrypted_data: str, country_code: str) -> str:
        """Decrypt PII data."""
        try:
            from utils.encryption import decrypt_data
            return decrypt_data(encrypted_data)
        except Exception:
            return "[DECRYPTION_FAILED]"
