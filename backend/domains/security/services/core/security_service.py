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
from domains.governance.models.fraud import DeviceFingerprint
from domains.governance.models.fraud import FraudBlacklist
from domains.governance.models.fraud import FraudEvent
from domains.governance.models.fraud import FraudRule
from domains.governance.models.fraud import IPReputation
from domains.governance.models.fraud import ManualReviewQueue
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


# === Merged from flat_admin_security_health_service.py ===

"""Risk Management Router."""
from __future__ import annotations
from fastapi import Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session
from rbac import detect_ghost_employees
from rbac import detect_impossible_travel
from rbac import update_flight_risk_score
from rbac import get_team_health_radar
from rbac import get_audit_timeline
from infrastructure.database.database import get_db

def get_risk_score(employee_id: int, db: Session=Depends(get_db)):
    """Return flight-risk / burnout score records for an employee (0 = all)."""
    if employee_id and employee_id != 0:
        rows = db.execute(text('\n                SELECT employee_id, metric_name, score, recorded_at\n                FROM employee_risk_scores\n                WHERE employee_id = :eid\n                ORDER BY recorded_at DESC\n            '), {'eid': employee_id}).fetchall()
    else:
        rows = db.execute(text('\n                SELECT employee_id, metric_name, score, recorded_at\n                FROM employee_risk_scores\n                ORDER BY recorded_at DESC\n                LIMIT 200\n            ')).fetchall()
    return [{'employee_id': r[0], 'metric_name': r[1], 'score': float(r[2]) if r[2] is not None else None, 'recorded_at': (r[3].isoformat() if not isinstance(r[3], str) else r[3]) if r[3] else None} for r in rows]


# === Merged from flat_admin_security_operations_service.py ===

"""
Incident War Room API
"""
from typing import Optional, Dict, Any
from fastapi import Depends
from sqlalchemy.orm import Session
from domains.governance.models.user import User
from domains.governance.models.incident import IncidentWarRoom
from domains.governance.services.incident.incident_service import get_incident_service
from domains.governance.services.incident.incident_service import IncidentService
from infrastructure.database.database import get_db
from rbac import get_current_user

async def get_war_room(war_room_id: int, current_user: dict=Depends(get_current_user), db: Session=Depends(get_db)):
    war_room = db.query(IncidentWarRoom).filter_by(id=war_room_id).first()
    if not war_room:
        return {'exists': False}
    return {'id': war_room.id, 'incident_id': war_room.incident_id, 'title': war_room.title, 'severity': war_room.severity, 'status': war_room.status, 'started_at': war_room.started_at.isoformat(), 'action_items': [{'id': a.id, 'title': a.title, 'status': a.status} for a in war_room.action_items]}


# === Merged from fraud_admin_service.py ===

"""Thin orchestration controller for fraud/security detection admin operations.

The ``routers.admin_security_detection`` router delegates to this controller so it
stays within the allowed circuit (routers -> controllers/schemas/auth-deps only).
Model construction and DB writes live here (the controller layer may use services
and models), while pure scoring still goes through ``services.security.fraud_detection_service``.
"""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session, sessionmaker
from infrastructure.database.session import SessionLocal

from domains.governance.models.fraud import FraudBlacklist
from domains.governance.models.fraud import FraudRule
from domains.governance.models.fraud import ManualReviewQueue
from domains.governance.models.fraud import IPReputation
import domains.comms.services as db_write
from infrastructure.database.schemas import ThreatFeedStatus

logger = logging.getLogger(__name__)


def _q(db: Session, model):
    return db.query(model)


def list_fraud_events(db: Session, page: int = 1, size: int = 50, user_id: Optional[int] = None, ip_address: Optional[str] = None, min_score: int = 0) -> list[dict]:
    from domains.governance.models.fraud import FraudEvent
    q = _q(db, FraudEvent)
    if user_id:
        q = q.filter(FraudEvent.user_id == user_id)
    if ip_address:
        q = q.filter(FraudEvent.ip_address == ip_address)
    if min_score > 0:
        q = q.filter(FraudEvent.fraud_score >= min_score)
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


def list_blacklist(db: Session, entity_type: Optional[str] = None, status: str = "active") -> list:
    q = _q(db, FraudBlacklist)
    if entity_type:
        q = q.filter(FraudBlacklist.entity_type == entity_type)
    q = q.filter(FraudBlacklist.status == status)
    rows = q.order_by(FraudBlacklist.created_at.desc()).all()
    return [{"id": r.id, "entity_type": r.entity_type, "entity_value_hash": r.entity_value_hash, "reason": r.reason, "status": r.status, "created_at": r.created_at, "expires_at": r.expires_at} for r in rows]


def add_to_blacklist(db: Session, payload: Any) -> FraudBlacklist:
    value_hash = hashlib.sha256(payload.entity_value.encode()).hexdigest()
    existing = _q(db, FraudBlacklist).filter(
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
    db_write.add(db, entry)
    db_write.commit(db)
    return entry


def remove_from_blacklist(db: Session, entry_id: int) -> dict:
    entry = _q(db, FraudBlacklist).filter(FraudBlacklist.id == entry_id).first()
    if not entry:
        raise HTTPException(404, "Entry not found")
    entry.status = "whitelisted"
    db_write.commit(db)
    return {"message": "Entity whitelisted"}


def list_rules(db: Session, is_active: bool = True) -> list:
    rows = _q(db, FraudRule).filter(FraudRule.is_active == is_active).all()
    return [{"id": r.id, "rule_key": r.rule_key, "name": r.name, "description": r.description, "weight": r.weight, "condition_json": r.condition_json, "is_active": r.is_active, "is_global": r.is_global, "country_code": r.country_code} for r in rows]


def list_review_queue(db: Session, status: str = "pending", priority: Optional[str] = None) -> list:
    q = _q(db, ManualReviewQueue).filter(ManualReviewQueue.status == status)
    if priority:
        q = q.filter(ManualReviewQueue.priority == priority)
    rows = q.order_by(ManualReviewQueue.priority.desc(), ManualReviewQueue.created_at.desc()).all()
    return [{"id": r.id, "status": r.status, "priority": r.priority, "assigned_to": r.assigned_to, "created_at": r.created_at} for r in rows]


def list_ip_reputation(db: Session, is_proxy: Optional[bool] = None, is_tor: Optional[bool] = None, limit: int = 100) -> list:
    q = _q(db, IPReputation)
    if is_proxy is not None:
        q = q.filter(IPReputation.is_proxy == is_proxy)
    if is_tor is not None:
        q = q.filter(IPReputation.is_tor == is_tor)
    rows = q.order_by(IPReputation.updated_at.desc()).limit(limit).all()
    return [{"ip_address": r.ip_address, "is_proxy": r.is_proxy, "is_tor": r.is_tor, "is_hosting": r.is_hosting, "updated_at": r.updated_at} for r in rows]


def list_device_fingerprints(db: Session, limit: int = 100, min_risk_score: int = 0) -> list:
    rows = _q(db, DeviceFingerprint).filter(DeviceFingerprint.risk_score >= min_risk_score).order_by(DeviceFingerprint.last_seen_at.desc()).limit(limit).all()
    return [{"device_hash": r.device_hash, "risk_score": r.risk_score, "last_seen_at": r.last_seen_at} for r in rows]


def create_rule(db: Session, payload: Any) -> FraudRule:
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
    db_write.add(db, rule)
    db_write.commit(db)
    return rule


def assign_review(db: Session, review_id: int, assignee_id: int) -> dict:
    review = _q(db, ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.assigned_to = assignee_id
    db_write.commit(db)
    return {"message": "Assigned"}


def resolve_review(db: Session, review_id: int, payload: Any, reviewed_by: int) -> dict:
    from datetime import datetime, timezone
    review = _q(db, ManualReviewQueue).filter(ManualReviewQueue.id == review_id).first()
    if not review:
        raise HTTPException(404, "Review not found")
    review.status = payload.status
    review.admin_notes = payload.admin_notes
    review.resolved_at = datetime.now(timezone.utc)
    review.reviewed_by = reviewed_by
    db_write.commit(db)
    return {"message": "Resolved"}


def threat_feed_status(db: Session) -> dict:
    tor_count = _q(db, IPReputation).filter(IPReputation.is_tor == True).count()
    proxy_count = _q(db, IPReputation).filter(IPReputation.is_proxy == True).count()
    hosting_count = _q(db, IPReputation).filter(IPReputation.is_hosting == True).count()
    return {"tor_count": tor_count, "proxy_count": proxy_count, "hosting_asn_count": hosting_count}
