"""Fraud admin operations for the fraud-detection admin command center.

All database reads/writes for the fraud admin surface live here (services
layer). Routers must NOT perform ``db.query`` / ``session.add`` / ``commit``
directly — they delegate through ``controllers.security.fraud_controller`` wrappers,
which call the functions in this module. This keeps the router layer a thin
HTTP/validation boundary (circuit LAYER 2 contract).

The ORM rows for ``blacklist`` / ``rules`` / ``ip_reputation`` /
``device_fingerprints`` / ``review_queue`` are returned as-is because their
``*Out`` schemas use ``from_attributes``; only ``list_fraud_events`` and
``get_threat_feed_status`` are projected into response schemas explicitly
(``triggered_rules`` is stored as a JSON string).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from domains.governance.models.fraud import DeviceFingerprint
from domains.governance.models.fraud import FraudBlacklist
from domains.governance.models.fraud import FraudEvent
from domains.governance.models.fraud import FraudRule
from domains.governance.models.fraud import IPReputation
from domains.governance.models.fraud import ManualReviewQueue
from infrastructure.database.schemas import FraudEventOut, ThreatFeedStatus
import structlog
logger = structlog.get_logger(__name__)


def list_fraud_events(
    db: Session,
    page: int = 1,
    size: int = 50,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None,
    min_score: int = 0,
) -> list[FraudEventOut]:
    q = db.query(FraudEvent)
    if user_id:
        q = q.filter(FraudEvent.user_id == user_id)
    if ip_address:
        q = q.filter(FraudEvent.ip_address == ip_address)
    if min_score > 0:
        q = q.filter(FraudEvent.fraud_score >= min_score)
    items = (
        q.order_by(FraudEvent.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
        .all()
    )
    return [
        FraudEventOut(
            id=e.id,
            user_id=e.user_id,
            event_type=e.event_type,
            ip_address=e.ip_address,
            device_hash=e.device_hash,
            fraud_score=e.fraud_score,
            triggered_rules=json.loads(e.triggered_rules) if e.triggered_rules else [],
            status=e.status,
            created_at=e.created_at,
        )
        for e in items
    ]


def list_blacklist(db: Session, entity_type: Optional[str] = None, status: str = "active") -> list:
    q = db.query(FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    return q.order_by(FraudBlacklist.created_at.desc()).all()


def add_to_blacklist(db: Session, entity_type: str, entity_value: str, reason: Optional[str], expires_at=None) -> FraudBlacklist:
    value_hash = hashlib.sha256(entity_value.encode()).hexdigest()
    existing = (
        db.query(FraudBlacklist)
        .filter(
            FraudBlacklist.entity_type == entity_type,
            FraudBlacklist.entity_value_hash == value_hash,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Entity already blacklisted")
    entry = FraudBlacklist(
        entity_type=entity_type,
        entity_value_hash=value_hash,
        reason=reason,
        expires_at=expires_at,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def remove_from_blacklist(db: Session, entry_id: int) -> None:
    entry = db.query(FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db.commit()


def list_rules(db: Session, is_active: bool = True) -> list:
    return db.query(FraudRule).filter(FraudRule.is_active == is_active).all()


def create_rule(
    db: Session,
    rule_key: str,
    name: str,
    description: Optional[str],
    weight: float,
    condition_json,
    is_active: bool,
    is_global: bool,
    country_code: Optional[str],
) -> FraudRule:
    rule = FraudRule(
        rule_key=rule_key,
        name=name,
        description=description,
        weight=weight,
        condition_json=json.dumps(condition_json) if condition_json else None,
        is_active=is_active,
        is_global=is_global,
        country_code=country_code,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_review_queue(db: Session, status: str = "pending", priority: Optional[str] = None) -> list:
    q = db.query(ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    return q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).all()


def assign_review(db: Session, review_id: int, assignee_id: int) -> None:
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.assigned_to = assignee_id
    db.commit()


def resolve_review(db: Session, review_id: int, status: str, admin_notes: Optional[str], reviewed_by: int) -> None:
    review = db.query(ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.status = status
    review.admin_notes = admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = reviewed_by
    db.commit()


def list_ip_reputation(db: Session, is_proxy: Optional[bool] = None, is_tor: Optional[bool] = None, limit: int = 100) -> list:
    q = db.query(IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    return q.order_by(IPReputation.updated_at.desc()).limit(limit).all()


def list_device_fingerprints(db: Session, limit: int = 100, min_risk_score: int = 0) -> list:
    return (
        db.query(DeviceFingerprint)
        .filter(DeviceFingerprint.risk_score >= min_risk_score)
        .order_by(DeviceFingerprint.last_seen_at.desc())
        .limit(limit)
        .all()
    )


def get_threat_feed_status(db: Session) -> ThreatFeedStatus:
    tor_count = db.query(IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = db.query(IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = db.query(IPReputation).filter(IPReputation.is_hosting == True).count()
    return ThreatFeedStatus(
        tor_count=tor_count,
        proxy_count=proxy_count,
        hosting_asn_count=hosting_count,
    )

