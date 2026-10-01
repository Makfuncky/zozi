"""Fraud Detection Engine — service layer (extracted from admin_security_detection router).

Holds all direct DB access for fraud/admin command-center reads and writes.
Routers delegate thin endpoints to these functions; the fraud *scoring* pipeline
lives in ``services.security.fraud_detection_service`` (FraudScoringEngine /
ThreatFeedUpdater) and is injected via FastAPI dependencies.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Query
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.security.models.fraud import DeviceFingerprint
from domains.security.models.fraud import FraudBlacklist
from domains.security.models.fraud import FraudEvent
from domains.security.models.fraud import FraudRule
from domains.security.models.fraud import IPReputation
from domains.security.models.fraud import ManualReviewQueue
from infrastructure.database.schemas import (
    FraudBlacklistCreate,
    FraudBlacklistOut,
    FraudDashboardStats,
    FraudEventOut,
    FraudRuleCreate,
    FraudRuleOut,
    IPReputationOut,
    DeviceFingerprintOut,
    ManualReviewOut,
    ManualReviewResolve,
    ThreatFeedStatus,
)


def list_fraud_events(
    page: int,
    size: int,
    user_id: Optional[int],
    ip_address: Optional[str],
    min_score: int,
    _=None,
    db: Session = Depends(get_db),
) -> list[dict]:
    """List fraud events with filtering."""
    q = db.query(FraudEvent)
    if user_id:
        q = q.filter(FraudEvent.user_id == user_id)
    if ip_address:
        q = q.filter(FraudEvent.ip_address == ip_address)
    if min_score > 0:
        q = q.filter(FraudEvent.fraud_score >= min_score)
    total = q.count()
    items = q.order_by(FraudEvent.created_at.desc()).offset((page - 1) * size).limit(size).all()

    results = []
    for e in items:
        results.append({
            "id": e.id,
            "user_id": e.user_id,
            "event_type": e.event_type,
            "ip_address": e.ip_address,
            "device_hash": e.device_hash,
            "fraud_score": e.fraud_score,
            "triggered_rules": json.loads(e.triggered_rules) if e.triggered_rules else [],
            "status": e.status,
            "created_at": e.created_at,
        })
    return results


def list_blacklist(
    entity_type: Optional[str],
    status: str,
    _=None,
    db: Session = Depends(get_db),
) -> list[FraudBlacklistOut]:
    """List blacklisted entities."""
    q = db.query(FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    return q.order_by(FraudBlacklist.created_at.desc()).all()


def add_to_blacklist(payload: FraudBlacklistCreate, _=None, db: Session = Depends(get_db)) -> FraudBlacklistOut:
    """Add entity to blacklist."""
    value_hash = hashlib.sha256(payload.entity_value.encode()).hexdigest()

    existing = db.query(FraudBlacklist).filter(
        FraudBlacklist.entity_type == payload.entity_type,
        FraudBlacklist.entity_value_hash == value_hash,
    ).first()
    if existing:
        raise HTTPException(400, "Entity already blacklisted")

    entry = FraudBlacklist(
        entity_type=payload.entity_type,
        entity_value_hash=value_hash,
        reason=payload.reason,
        expires_at=payload.expires_at,
    )
    db.add(entry)
    db.commit()
    return entry


def remove_from_blacklist(entry_id: int, _=None, db: Session = Depends(get_db)) -> dict:
    """Remove entity from blacklist (whitelist)."""
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db.commit()
    return {"message": "Entity whitelisted"}


def list_rules(is_active: bool, _=None, db: Session = Depends(get_db)) -> list[FraudRuleOut]:
    """List fraud detection rules."""
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).all()


def create_rule(payload: FraudRuleCreate, _=None, db: Session = Depends(get_db)) -> FraudRuleOut:
    """Create a new fraud detection rule."""
    rule = FraudRule(
        rule_key=payload.rule_key,
        name=payload.name,
        description=payload.description,
        weight=payload.weight,
        condition_json=json.dumps(payload.condition_json) if payload.condition_json else None,
        is_active=payload.is_active,
        is_global=payload.is_global,
        country_code=payload.country_code,
    )
    db.add(rule)
    db.commit()
    return rule


def list_review_queue(
    status: str,
    priority: Optional[str],
    _=None,
    db: Session = Depends(get_db),
) -> list[ManualReviewOut]:
    """List items pending manual review."""
    q = db.query(ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    return q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).all()


def assign_review(review_id: int, assignee_id: int, _=None, db: Session = Depends(get_db)) -> dict:
    """Assign review to an admin."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.assigned_to = assignee_id
    db.commit()
    return {"message": "Assigned"}


def resolve_review(review_id: int, payload: ManualReviewResolve, current_user=None, db: Session = Depends(get_db)) -> dict:
    """Resolve a manual review."""
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.status = payload.status
    review.admin_notes = payload.admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = current_user.id
    db.commit()
    return {"message": "Resolved"}


def list_ip_reputation(
    is_proxy: Optional[bool],
    is_tor: Optional[bool],
    limit: int,
    _=None,
    db: Session = Depends(get_db),
) -> list[IPReputationOut]:
    """List IP reputation records."""
    q = db.query(IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    return q.order_by(IPReputation.updated_at.desc()).limit(limit).all()


def list_device_fingerprints(
    limit: int,
    min_risk_score: int,
    _=None,
    db: Session = Depends(get_db),
) -> list[DeviceFingerprintOut]:
    """List device fingerprint records."""
    return db.query(DeviceFingerprint).filter(
        DeviceFingerprint.risk_score >= min_risk_score,
    ).order_by(DeviceFingerprint.last_seen_at.desc()).limit(limit).all()


def get_threat_feed_status(db: Session = Depends(get_db)) -> ThreatFeedStatus:
    """Get threat feed status."""
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()  # noqa: E712
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()  # noqa: E712
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()  # noqa: E712

    return ThreatFeedStatus(
        tor_count=tor_count,
        proxy_count=proxy_count,
        hosting_asn_count=hosting_count,
    )

