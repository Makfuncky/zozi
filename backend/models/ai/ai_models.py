"""AI service models (ADR-021).

Centralised AI staging, request, result, and embedding tables in the ``ai``
schema.  ``ai_requests`` and ``ai_results`` are monthly range-partitioned
(DB23 pattern) — high write volume.  ``ai_embeddings`` is NOT partitioned
— queried by vector similarity, not time.
"""
from __future__ import annotations

import uuid as _uuid

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from .. import Base
from utils.datetime_utils import utcnow as _utcnow
from ..mixins import TenantMixin


__all__ = ["AIEmbedding", "AIRequest", "AIResult"]


class AIEmbedding(Base):
    """Embedding vectors stored for similarity search (ADR-008 — pgvector).

    Not partitioned — queried by vector similarity, not time range.
    """
    __tablename__ = "ai_embeddings"
    __table_args__ = (
        Index("ix_ai_embeddings_source", "source_type", "source_id"),
        {"schema": "ai"},
    )

    id = Column(String(36), primary_key=True, index=True,
                default=lambda: str(_uuid.uuid4()))
    source_type = Column(String(50), nullable=False, index=True)
    source_id = Column(String(100), nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    vector = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)


class AIRequest(Base, TenantMixin):
    """AI request log — partitioned monthly by created_at (DB23).

    Every call to an AI provider is logged here *before* the call so that
    cost attribution and audit are durable even if the provider call fails.
    """
    __tablename__ = "ai_requests"
    __table_args__ = ({"schema": "ai"},)

    __partition_by__ = "range"
    __partition_key__ = "created_at"

    id = Column(String(36), primary_key=True, index=True,
                default=lambda: str(_uuid.uuid4()))
    provider = Column(String(50), nullable=False, index=True)
    model = Column(String(100), nullable=False)
    prompt = Column(Text, nullable=False)
    request_metadata = Column("metadata", JSON, nullable=True)
    user_id = Column(Integer, nullable=True, index=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)

    results = relationship("AIResult", back_populates="request",
                           cascade="all, delete-orphan")


class AIResult(Base, TenantMixin):
    """AI result log — partitioned monthly by created_at (DB23).

    Records the response, token consumption, cost, and latency for each
    AI request.  Links to ``ai_requests`` via ``request_id``.
    """
    __tablename__ = "ai_results"
    __table_args__ = ({"schema": "ai"},)

    __partition_by__ = "range"
    __partition_key__ = "created_at"

    id = Column(String(36), primary_key=True, index=True,
                default=lambda: str(_uuid.uuid4()))
    request_id = Column(String(36), ForeignKey("ai.ai_requests.id"),
                        nullable=False, index=True)
    response = Column(Text, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    cost_cents = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=False, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    created_at = Column(DateTime, default=_utcnow, nullable=False, index=True)

    request = relationship("AIRequest", back_populates="results")
