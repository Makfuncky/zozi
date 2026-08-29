"""logistics domain — shipping rules previously housed under country.

These models were originally defined in ``domains/country/models/countries.py``.
They describe logistics-domain concepts (shipping rules) and have been
relocated here to remove cross-domain pollution.

The ``__tablename__`` and underlying Postgres schema are preserved unchanged so that
no Alembic migration is required for this move. Future migrations may move the
physical tables to the ``logistics`` schema.
"""
from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Numeric, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as utcnow

__all__ = ["ShippingRule"]


class ShippingRule(Base):
    __tablename__ = 'shipping_rules'
    __table_args__ = (Index('ix_shipping_rules_country_created', 'country_code', 'created_at'), {'schema': 'logistics'})
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey('country.country_configs.code', ondelete='RESTRICT'), nullable=False)
    method = Column(String(50), nullable=False)
    base_rate = Column(Numeric(10, 2), nullable=False)
    per_kg_rate = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)
    country = relationship('CountryConfig', back_populates='shipping_rules')
