"""Transactional outbox / inbox / retry / DLQ event models (Constitution §2.13, ADR-014).

Pattern: a service writes to ``outbox_events`` in the same transaction as the
business write; a relay publishes to the broker; consumers record ``inbox_events``
for idempotency; transient failures flow to ``event_retry_queue``; permanent
failures flow to ``event_dead_letter`` for manual review. This is how the
commerce / logistics / finance / analytics ecosystems talk without cross-FK chains.
"""
from __future__ import annotations

import uuid as _uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from utils.datetime_utils import utcnow as _utcnow

from . import Base

__all__ = ["OutboxEvent", "InboxEvent", "EventRetryQueue", "EventDeadLetter"]


class OutboxEvent(Base):
    """Durable event written transactionally alongside the business write."""
    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
        Index("ix_outbox_status", "status", "created_at"),
        Index("ix_outbox_country", "country_code"),
        UniqueConstraint("uuid", name="uq_outbox_uuid"),
        {"schema": "configuration"},
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(_uuid.uuid4()))
    event_type = Column(String(100), nullable=False, index=True)
    aggregate_type = Column(String(50), nullable=False)
    aggregate_id = Column(Integer, nullable=False)
    payload_json = Column(Text, nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending | published | failed
    country_code = Column(String(3), nullable=True, index=True)
    published_at = Column(DateTime, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    # Cross-ecosystem reference by user ID — NO foreign key (ADR-014:
    # cross-ecosystem communication uses services/events, not cross-FKs).
    # The integer is resolvable via the core.users service; the DB does not
    # enforce the constraint so the configuration and core ecosystems stay decoupled.
    deleted_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)

    deleted_by = relationship("User", foreign_keys=[deleted_by_id], primaryjoin="OutboxEvent.deleted_by_id==User.id")
    created_by = relationship("User", foreign_keys=[created_by_id], primaryjoin="OutboxEvent.created_by_id==User.id")
    updated_by = relationship("User", foreign_keys=[updated_by_id], primaryjoin="OutboxEvent.updated_by_id==User.id")


class InboxEvent(Base):
    """Consumer-side deduplication ledger for processed events."""
    __tablename__ = "inbox_events"
    __table_args__ = (
        Index("ix_inbox_event_type", "event_type"),
        Index("ix_inbox_processed", "processed_at"),
        Index("ix_inbox_country", "country_code"),
        UniqueConstraint("idempotency_key", name="uq_inbox_idempotency_key"),
        {"schema": "configuration"},
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(_uuid.uuid4()))
    idempotency_key = Column(String(64), nullable=False, unique=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    processed_at = Column(DateTime, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    deleted_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)

    deleted_by = relationship("User", foreign_keys=[deleted_by_id], primaryjoin="InboxEvent.deleted_by_id==User.id")
    created_by = relationship("User", foreign_keys=[created_by_id], primaryjoin="InboxEvent.created_by_id==User.id")
    updated_by = relationship("User", foreign_keys=[updated_by_id], primaryjoin="InboxEvent.updated_by_id==User.id")


class EventRetryQueue(Base):
    """Transient-failure retry scheduling with exponential backoff."""
    __tablename__ = "event_retry_queue"
    __table_args__ = (
        Index("ix_retry_event", "event_id"),
        Index("ix_retry_next_attempt", "next_attempt_at"),
        Index("ix_retry_country", "country_code"),
        {"schema": "configuration"},
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(_uuid.uuid4()))
    event_id = Column(Integer, ForeignKey("configuration.outbox_events.id", ondelete="CASCADE"), nullable=False, index=True)
    attempt = Column(Integer, nullable=False, default=1)
    next_attempt_at = Column(DateTime, nullable=False)
    last_error = Column(Text, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    # Cross-ecosystem user references — no FK (ADR-014).
    deleted_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)

    event = relationship("OutboxEvent", foreign_keys=[event_id])
    deleted_by = relationship("User", foreign_keys=[deleted_by_id], primaryjoin="EventRetryQueue.deleted_by_id==User.id")
    created_by = relationship("User", foreign_keys=[created_by_id], primaryjoin="EventRetryQueue.created_by_id==User.id")
    updated_by = relationship("User", foreign_keys=[updated_by_id], primaryjoin="EventRetryQueue.updated_by_id==User.id")


class EventDeadLetter(Base):
    """Permanent-failure queue requiring manual review."""
    __tablename__ = "event_dead_letter"
    __table_args__ = (
        Index("ix_dlq_event", "event_id"),
        Index("ix_dlq_failed", "failed_at"),
        Index("ix_dlq_country", "country_code"),
        {"schema": "configuration"},
    )

    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), nullable=False, unique=True, index=True, default=lambda: str(_uuid.uuid4()))
    event_id = Column(Integer, ForeignKey("configuration.outbox_events.id", ondelete="CASCADE"), nullable=False, index=True)
    payload_json = Column(Text, nullable=False)
    failed_at = Column(DateTime, default=_utcnow, nullable=False)
    reason = Column(String(255), nullable=True)
    resolved_by = Column(Integer, nullable=True)
    country_code = Column(String(3), nullable=True, index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=_utcnow, nullable=False)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=False)
    is_deleted = Column(Boolean, nullable=False, default=False)
    deleted_at = Column(DateTime, nullable=True)
    delete_reason = Column(Text, nullable=True)

    # Cross-ecosystem user references — no FK (ADR-014).
    deleted_by_id = Column(Integer, nullable=True, index=True)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)

    event = relationship("OutboxEvent", foreign_keys=[event_id])
    resolver = relationship("User", foreign_keys=[resolved_by], primaryjoin="EventDeadLetter.resolved_by==User.id")
    deleted_by = relationship("User", foreign_keys=[deleted_by_id], primaryjoin="EventDeadLetter.deleted_by_id==User.id")
    created_by = relationship("User", foreign_keys=[created_by_id], primaryjoin="EventDeadLetter.created_by_id==User.id")
    updated_by = relationship("User", foreign_keys=[updated_by_id], primaryjoin="EventDeadLetter.updated_by_id==User.id")
