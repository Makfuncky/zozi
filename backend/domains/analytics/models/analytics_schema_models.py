
from __future__ import annotations

import uuid
from sqlalchemy import Column, DateTime, Integer, String, Text, Boolean, Index, func
from infrastructure.database.base import Base  # noqa: A003  (DG2: import Base directly to break the models-package cycle)

# Canonical home for the ``analytics`` and ``ai`` schemas (A3 / S26 ACC-01).
# Both are cross-cutting "intelligence" capabilities, grouped per-capability.
#
# NOTE on mixins: ExecutiveNews already declares ``country_code`` + ``created_at``
# and PredictiveSimulation declares ``created_at``, so we add the standard column
# set MANUALLY (mirroring migration 2026_08_06_0001) instead of inheriting
# AuditMixin/TenantMixin, which would redeclare those columns and raise
# "column already defined" at mapper configuration time (DBA03).

__all__ = ["ExecutiveNews", "PredictiveSimulation"]

# NOTE: ``FinancialReport`` was removed from this module. The canonical model
# lives in ``domains/finance/models/general_ledger.py`` (Law 6: schema = owning
# domain, and financial reports are owned by the finance domain).


def _new_uuid() -> str:
    return str(uuid.uuid4())


class ExecutiveNews(Base):
    __tablename__ = "executive_news"
    __table_args__ = (
        Index("ix_executive_news_country_created", "country_code", "created_at"),  # DBA31
        {"extend_existing": True, "schema": "analytics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), nullable=True)
    category = Column(String(50), default="general")
    priority = Column(String(20), default="normal")
    country_code = Column(String(2), nullable=True)
    is_published = Column(Boolean, default=False)
    ai_sentiment = Column(String(20), default="neutral")
    published_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # --- standard column set (DBA03) added manually to avoid mixin column clash ---
    uuid = Column(String(36), unique=True, index=True, default=_new_uuid)
    version = Column(Integer, nullable=False, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by_id = Column(Integer, nullable=True)


class PredictiveSimulation(Base):
    __tablename__ = "predictive_simulations"
    __table_args__ = (
        Index("ix_predictive_simulations_country_created", "country_code", "created_at"),  # DBA31
        {"extend_existing": True, "schema": "analytics"},
    )
    id = Column(Integer, primary_key=True, index=True)
    simulation_type = Column(String(50), nullable=False)
    parameters_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    # --- standard column set (DBA03) added manually ---
    uuid = Column(String(36), unique=True, index=True, default=_new_uuid)
    version = Column(Integer, nullable=False, default=1)
    created_by_id = Column(Integer, nullable=True, index=True)
    updated_by_id = Column(Integer, nullable=True, index=True)
    deleted_at = Column(DateTime, nullable=True, index=True)
    deleted_by_id = Column(Integer, nullable=True)
