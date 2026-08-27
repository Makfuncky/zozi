"""Comprehensive fraud detection and prevention service."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from domains.governance.models.user import UserLoginHistory
from domains.security.models.fraud import FraudEvent
from domains.security.models.fraud import FraudBlacklist
from domains.security.models.fraud import FraudRule
from domains.security.models.fraud import ManualReviewQueue
from domains.security.models.fraud import IPReputation
from domains.security.models.fraud import DeviceFingerprint
from domains.security.models.fraud import CreditCardBin
from domains.security.models.fraud import ReturnAbusePattern
from domains.security.models.fraud import SupplierFraudIndicator
from domains.security.models.fraud import LogisticsFraudIndicator
from domains.security.models.fraud import FraudAlert
from domains.security.models.fraud import IPAccountLinkage


class FraudService:
    """Service for fraud detection, prevention, and management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_fraud_event(
        self,
        user_id: Optional[int],
        event_type: str,
        ip_address: Optional[str],
        fraud_score: int,
        triggered_rules: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> FraudEvent:
        event = FraudEvent(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            fraud_score=fraud_score,
            triggered_rules=triggered_rules and ",".join(triggered_rules),
            details=str(details) if details else None,
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event
    
    def check_blacklist(self, identifier_type: str, identifier_value: str) -> bool:
        """Check if identifier is blacklisted."""
        import hashlib
        value_hash = hashlib.sha256(identifier_value.encode()).hexdigest()
        blacklisted = (
            self.db.query(FraudBlacklist)
            .filter(
                FraudBlacklist.identifier_type == identifier_type,
                FraudBlacklist.identifier_value_hash == value_hash,
                FraudBlacklist.is_active == True,
            )
            .first()
        )
        if blacklisted and blacklisted.expires_at:
            if blacklisted.expires_at < datetime.now(timezone.utc):
                return False
        return blacklisted is not None
    
    def get_fraud_rules(self) -> List[FraudRule]:
        """Get active fraud rules."""
        return (
            self.db.query(FraudRule)
            .filter(FraudRule.is_active == True)
            .all()
        )
    
    def create_manual_review(
        self,
        entity_type: str,
        entity_id: int,
        fraud_score: int,
        triggered_rules: Optional[List[str]] = None,
    ) -> ManualReviewQueue:
        """Create a manual review task."""
        review = ManualReviewQueue(
            entity_type=entity_type,
            entity_id=entity_id,
            fraud_score=fraud_score,
            triggered_rules=",".join(triggered_rules) if triggered_rules else None,
        )
        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)
        return review
    
    def update_ip_reputation(
        self,
        ip_address: str,
        is_proxy: bool = False,
        is_tor: bool = False,
        is_vpn: bool = False,
        is_hosting: bool = False,
        country_code: str = None,
    ) -> IPReputation:
        """Update IP reputation record."""
        existing = (
            self.db.query(IPReputation)
            .filter(IPReputation.ip_address == ip_address)
            .first()
        )
        if existing:
            existing.is_proxy = is_proxy
            existing.is_tor = is_tor
            existing.is_vpn = is_vpn
            existing.is_hosting = is_hosting
            existing.country_code = country_code
            existing.last_seen = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        reputation = IPReputation(
            ip_address=ip_address,
            is_proxy=is_proxy,
            is_tor=is_tor,
            is_vpn=is_vpn,
            is_hosting=is_hosting,
            country_code=country_code,
        )
        self.db.add(reputation)
        self.db.commit()
        self.db.refresh(reputation)
        return reputation
    
    def record_login(
        self,
        user_id: Optional[int],
        ip_address: str,
        user_agent: str,
        success: bool,
    ) -> UserLoginHistory:
        """Record a login attempt."""
        login = UserLoginHistory(
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
        )
        self.db.add(login)
        self.db.commit()
        self.db.refresh(login)
        return login
    
    def create_fraud_alert(
        self,
        alert_type: str,
        entity_type: str,
        entity_id: int,
        fraud_score: int,
        priority: str = "medium",
    ) -> FraudAlert:
        """Create a fraud alert."""
        alert = FraudAlert(
            alert_type=alert_type,
            entity_type=entity_type,
            entity_id=entity_id,
            fraud_score=fraud_score,
            priority=priority,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert


def create_fraud_service(db: Session) -> FraudService:
    return FraudService(db)


def list_fraud_events(
    db: Session,
    page: int,
    size: int,
    user_id: int | None,
    ip_address: str | None,
    min_score: int,
) -> list:
    from domains.security.models.fraud import FraudEvent
    query = db.query(FraudEvent)
    if user_id:
        query = query.filter(FraudEvent.user_id == user_id)
    if ip_address:
        query = query.filter(FraudEvent.ip_address == ip_address)
    if min_score:
        query = query.filter(FraudEvent.score >= min_score)
    return query.order_by(FraudEvent.created_at.desc()).offset((page - 1) * size).limit(size).all()


def list_blacklist(db: Session, entity_type: str | None, status: str) -> list:
    from domains.security.models.fraud import FraudBlacklist
    query = db.query(FraudBlacklist)
    if entity_type:
        query = query.filter(FraudBlacklist.entity_type == entity_type)
    if status:
        query = query.filter(FraudBlacklist.status == status)
    return query.all()


def add_to_blacklist(db: Session, payload: dict):
    import hashlib
    from fastapi import HTTPException
    from domains.security.models.fraud import FraudBlacklist
    value_hash = hashlib.sha256(payload["entity_value"].encode()).hexdigest()
    existing = db.query(FraudBlacklist).filter(
        FraudBlacklist.entity_type == payload["entity_type"],
        FraudBlacklist.entity_value_hash == value_hash,
    ).first()
    if existing:
        raise HTTPException(400, "Entity already blacklisted")
    entry = FraudBlacklist(
        entity_type=payload["entity_type"],
        entity_value_hash=value_hash,
        reason=payload.get("reason"),
        expires_at=payload.get("expires_at"),
    )
    db.add(entry)
    db.commit()
    return entry


def remove_from_blacklist(db: Session, entry_id: int):
    from fastapi import HTTPException
    from domains.security.models.fraud import FraudBlacklist
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db.commit()
    return {"message": "Entity whitelisted"}


def list_rules(db: Session, is_active: bool) -> list:
    from domains.security.models.fraud import FraudRule
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).all()


def list_review_queue(db: Session, status: str, priority: str | None) -> list:
    from domains.security.models.fraud import ManualReviewQueue
    query = db.query(ManualReviewQueue)
    if status:
        query = query.filter(ManualReviewQueue.status == status)
    if priority:
        query = query.filter(ManualReviewQueue.priority == priority)
    return query.all()


def get_threat_feed_status(db: Session) -> dict:
    from domains.security.models.fraud import IPReputation
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()
    return {
        "tor_count": tor_count,
        "proxy_count": proxy_count,
        "hosting_asn_count": hosting_count,
    }

