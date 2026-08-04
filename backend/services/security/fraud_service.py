"""Comprehensive fraud detection and prevention service."""

from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from data.models import (
    FraudEvent, FraudBlacklist, FraudRule, ManualReviewQueue,
    IPReputation, DeviceFingerprint, UserLoginHistory,
    CreditCardBin, ReturnAbusePattern, SupplierFraudIndicator,
    LogisticsFraudIndicator, FraudAlert, IPAccountLinkage
)


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
    
    def check_blacklist(self, entity_type: str, entity_value: str) -> bool:
        """Check if entity is blacklisted."""
        blacklisted = (
            self.db.query(FraudBlacklist)
            .filter(
                FraudBlacklist.entity_type == entity_type,
                FraudBlacklist.entity_value == entity_value,
                FraudBlacklist.is_active == True,
            )
            .first()
        )
        if blacklisted and blacklisted.expires_at:
            if blacklisted.expires_at < datetime.utcnow():
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
            existing.last_seen = datetime.utcnow()
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

