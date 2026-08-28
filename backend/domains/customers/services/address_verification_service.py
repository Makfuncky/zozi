"""Address verification service — minimal verification workflow.

The customers domain owns address data via ``accounts.Address`` (read through
``accounts.ports`` per Law 3). This service records verification state on the
address row using lightweight columns it already exposes (``is_default`` and
metadata); the verification status is computed deterministically from a
per-address last-verified timestamp stored as an attribute on the address.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from domains.accounts.ports import Address
from infrastructure.utils.datetime_utils import utcnow
import structlog

logger = structlog.get_logger(__name__)


_VERIFICATION_TTL = timedelta(days=180)


def _serialize_status(address: Address) -> Dict[str, Any]:
    last_verified = getattr(address, "updated_at", None)
    if last_verified is None:
        return {
            "address_id": address.id,
            "status": "unverified",
            "last_verified_at": None,
        }
    age = utcnow() - last_verified
    status_label = "verified" if age <= _VERIFICATION_TTL else "stale"
    return {
        "address_id": address.id,
        "status": status_label,
        "last_verified_at": last_verified,
    }


class AddressVerificationService:
    """Service facade for address-verification read/update."""

    def __init__(self, db: Session):
        self.db = db

    def verify_address(self, address_id: int, user_id: int) -> Dict[str, Any]:
        """Mark ``address_id`` (owned by ``user_id``) as verified."""
        address = (
            self.db.query(Address)
            .filter(Address.id == int(address_id), Address.user_id == int(user_id))
            .first()
        )
        if address is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        address.updated_at = utcnow()
        self.db.add(address)
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            logger.error(
                "address_verify.failed",
                address_id=address_id,
                user_id=user_id,
                error=str(exc),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify address.",
            ) from exc
        self.db.refresh(address)
        return {
            "address_id": address.id,
            "status": "verified",
            "last_verified_at": address.updated_at,
        }

    def get_verification_status(self, address_id: int, user_id: int) -> Dict[str, Any]:
        """Return the current verification status for the address."""
        address = (
            self.db.query(Address)
            .filter(Address.id == int(address_id), Address.user_id == int(user_id))
            .first()
        )
        if address is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address not found.",
            )
        return _serialize_status(address)
