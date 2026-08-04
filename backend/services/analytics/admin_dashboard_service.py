"""
Automatic service for admin_dashboard_service - DB read operations delegated from controllers.
"""

from typing import Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, desc, asc

from data.models import *
from data.services_write_helpers import add_and_flush, commit_only

def get_adminanalyticssnapshot_by_condition(db: Session, **filters) -> Optional[AdminAnalyticsSnapshot]:
    query = db.query(AdminAnalyticsSnapshot)
    for key, value in filters.items():
        query = query.filter(getattr(AdminAnalyticsSnapshot, key) == value)
    return query.first()


def get_unknown_first(db: Session, **filters) -> Optional[Unknown]:
    query = db.query(Unknown)
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.limit(1).first()


def get_user_first(db: Session, **filters) -> Optional[User]:
    query = db.query(User)
    for key, value in filters.items():
        query = query.filter(getattr(User, key) == value)
    return query.limit(1).first()


def get_chatbotqueryevent_first(db: Session, **filters) -> Optional[ChatbotQueryEvent]:
    query = db.query(ChatbotQueryEvent)
    for key, value in filters.items():
        query = query.filter(getattr(ChatbotQueryEvent, key) == value)
    return query.limit(1).first()


def get_unknown_scalar(db: Session, column: str, **filters) -> Any:
    query = db.query(getattr(Unknown, column))
    for key, value in filters.items():
        query = query.filter(getattr(Unknown, key) == value)
    return query.scalar()

def _db_adminanalyticssnapshot_first_0(db: Session, snapshot_key: Any) -> Optional[Any]:
    result = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    return result
    """Read-only query delegated from controller."""

def _db_adminanalyticssnapshot_first_1(db: Session, snapshot_key: Any) -> Optional[Any]:
    result = db.query(AdminAnalyticsSnapshot).filter(AdminAnalyticsSnapshot.snapshot_key == snapshot_key).first()
    return result
    """Read-only query delegated from controller."""

def _db_chatbotqueryevent_query_2(db: Session) -> Optional[Any]:
    return db.query(ChatbotQueryEvent)
    """Read-only query delegated from controller."""
