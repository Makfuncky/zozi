"""
WORM-Compliant Immutable Audit Trail
Features: Append-only storage, cryptographic sealing, chain-of-custody
"""
import hashlib
import hmac
from contextlib import nullcontext
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from domains.audit.ports import AuditLog
from infrastructure.utils.config import settings
import structlog
logger = structlog.get_logger(__name__)


class WORMAuditService:
    """Write-Once-Read-Many compliant audit trail."""

    def __init__(self, db: Session = None):
        self.db = db
        self._chain_key = (settings.audit_chain_key or settings.secret_key or "zozi_audit_chain").encode()
        self._last_hash = self._get_chain_tail_hash()

    def _session_ctx(self):
        if self.db is not None:
            return nullcontext(self.db)
        from infrastructure.database.database import get_service_session
        return get_service_session()

    def _compute_chain_hash_for(self, prev_hash: str, record_hash: str) -> str:
        chain_input = f"{prev_hash}|{record_hash}"
        return hmac.new(
            self._chain_key,
            chain_input.encode(),
            hashlib.sha256
        ).hexdigest()

    def append(
        self,
        action: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        user_role: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        country_code: Optional[str] = None,
    ) -> AuditLog:
        """Append an immutable audit record."""
        with self._session_ctx() as db:
            record = AuditLog(
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                username=username,
                user_role=user_role,
                details=details,
                ip_address=ip_address,
                country_code=country_code,
            )
            db.add(record)
            db.flush()

            record_hash = self._compute_record_hash(record)
            prev_hash = self._last_hash
            record_hash_chain = self._compute_chain_hash_for(prev_hash, record_hash)

            sealed_details = dict(record.details or {})
            sealed_details["worm_hash"] = record_hash_chain
            sealed_details["worm_prev_hash"] = prev_hash
            record.details = sealed_details

            record.worm_hash = record_hash_chain
            record.worm_prev_hash = prev_hash

            db.commit()
            self._last_hash = record_hash_chain

            logger.info(f"WORM audit appended: {action} on {entity_type}:{entity_id}")
            return record

    def get_chain_integrity(self) -> Dict[str, Any]:
        """Verify audit trail chain integrity."""
        with self._session_ctx() as db:
            records = db.query(AuditLog).order_by(AuditLog.id.asc()).all()

        worm_records = []
        for r in records:
            details = r.details or {}
            if getattr(r, "worm_hash", None) is not None or "worm_hash" in details:
                worm_records.append(r)

        if not worm_records:
            return {
                "total_records": 0,
                "chain_valid": True,
                "last_hash": self._last_hash,
                "first_break": None,
            }

        expected_prev = hashlib.sha256("genesis".encode()).hexdigest()
        for r in worm_records:
            details = r.details or {}
            stored_hash = getattr(r, "worm_hash", None)
            if stored_hash is None:
                stored_hash = details.get("worm_hash")

            stored_prev_hash = getattr(r, "worm_prev_hash", None)
            if stored_prev_hash is None:
                stored_prev_hash = details.get("worm_prev_hash")

            if stored_prev_hash != expected_prev:
                return {
                    "total_records": len(worm_records),
                    "chain_valid": False,
                    "last_hash": self._last_hash,
                    "first_break": {
                        "record_id": r.id,
                        "expected_prev_hash": expected_prev,
                        "actual_prev_hash": stored_prev_hash,
                    },
                }

            recomputed_record_hash = self._compute_record_hash(r)
            expected_chain_hash = self._compute_chain_hash_for(expected_prev, recomputed_record_hash)

            if stored_hash != expected_chain_hash:
                return {
                    "total_records": len(worm_records),
                    "chain_valid": False,
                    "last_hash": self._last_hash,
                    "first_break": {
                        "record_id": r.id,
                        "expected_hash": expected_chain_hash,
                        "actual_hash": stored_hash,
                    },
                }

            expected_prev = stored_hash

        return {
            "total_records": len(worm_records),
            "chain_valid": True,
            "last_hash": self._last_hash,
            "first_break": None,
        }

    def _compute_record_hash(self, record: AuditLog) -> str:
        """Compute SHA-256 hash of a single audit record."""
        data = f"{record.id}|{record.action}|{record.entity_type}|{record.entity_id}|{record.created_at.isoformat() if record.created_at else ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    def _compute_chain_hash(self, record_hash: str) -> str:
        """Compute chain hash linking to previous record."""
        return self._compute_chain_hash_for(self._last_hash, record_hash)

    def _get_chain_tail_hash(self) -> str:
        """Get the hash of the most recent record in the chain."""
        with self._session_ctx() as db:
            records = db.query(AuditLog).order_by(AuditLog.id.desc()).all()
            for r in records:
                col_hash = getattr(r, "worm_hash", None)
                if col_hash:
                    return col_hash
                details = r.details or {}
                if "worm_hash" in details:
                    return details["worm_hash"]
        return hashlib.sha256("genesis".encode()).hexdigest()


def get_worm_audit_service(db: Session = None) -> WORMAuditService:
    return WORMAuditService(db)
