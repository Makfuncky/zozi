"""Fraud controller: thin delegation layer between routers and the fraud service.

Routers call these wrappers instead of touching the session directly. The
wrappers perform no DB writes of their own — they forward ``db`` to
``services.fraud_admin_service`` (circuit LAYER 3 contract: controllers may
call services).
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy.orm import Session

from services.fraud_admin_service import (
    add_to_blacklist as _add_to_blacklist,
    assign_review as _assign_review,
    create_rule as _create_rule,
    get_threat_feed_status as _get_threat_feed_status,
    list_blacklist as _list_blacklist,
    list_device_fingerprints as _list_device_fingerprints,
    list_fraud_events as _list_fraud_events,
    list_ip_reputation as _list_ip_reputation,
    list_review_queue as _list_review_queue,
    list_rules as _list_rules,
    remove_from_blacklist as _remove_from_blacklist,
    resolve_review as _resolve_review,
)
import structlog
logger = structlog.get_logger(__name__)


def fraud_list_events(db: Session, page: int = 1, size: int = 50, user_id: Optional[int] = None, ip_address: Optional[str] = None, min_score: int = 0):
    return _list_fraud_events(db, page=page, size=size, user_id=user_id, ip_address=ip_address, min_score=min_score)


def fraud_list_blacklist(db: Session, entity_type: Optional[str] = None, status: str = "active"):
    return _list_blacklist(db, entity_type=entity_type, status=status)


def fraud_add_blacklist(db: Session, entity_type: str, entity_value: str, reason: Optional[str], expires_at=None):
    return _add_to_blacklist(db, entity_type, entity_value, reason, expires_at)


def fraud_remove_blacklist(db: Session, entry_id: int) -> None:
    _remove_from_blacklist(db, entry_id)


def fraud_list_rules(db: Session, is_active: bool = True):
    return _list_rules(db, is_active=is_active)


def fraud_create_rule(db: Session, rule_key: str, name: str, description: Optional[str], weight: float, condition_json, is_active: bool, is_global: bool, country_code: Optional[str]):
    return _create_rule(db, rule_key, name, description, weight, condition_json, is_active, is_global, country_code)


def fraud_list_review_queue(db: Session, status: str = "pending", priority: Optional[str] = None):
    return _list_review_queue(db, status=status, priority=priority)


def fraud_assign_review(db: Session, review_id: int, assignee_id: int) -> None:
    _assign_review(db, review_id, assignee_id)


def fraud_resolve_review(db: Session, review_id: int, status: str, admin_notes: Optional[str], reviewed_by: int) -> None:
    _resolve_review(db, review_id, status, admin_notes, reviewed_by)


def fraud_list_ip_reputation(db: Session, is_proxy: Optional[bool] = None, is_tor: Optional[bool] = None, limit: int = 100):
    return _list_ip_reputation(db, is_proxy=is_proxy, is_tor=is_tor, limit=limit)


def fraud_list_device_fingerprints(db: Session, limit: int = 100, min_risk_score: int = 0):
    return _list_device_fingerprints(db, limit=limit, min_risk_score=min_risk_score)


def fraud_threat_feed_status(db: Session):
    return _get_threat_feed_status(db)
