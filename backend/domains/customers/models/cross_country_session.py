"""customers domain — cross-country customer session model previously housed under country.

This table was originally defined in ``domains/country/models/country_enhancements.py``.
It is a customer-domain concept and has been relocated here to remove cross-domain pollution.

The ``__tablename__`` and underlying Postgres schema are preserved unchanged so that
no Alembic migration is required for this move. Future migrations may move the
physical table to the ``customers`` schema.
"""
from __future__ import annotations
from uuid import uuid4
from sqlalchemy import func, UUID
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import relationship
from infrastructure.database.types import GUID
from . import Base
from infrastructure.utils.datetime_utils import utcnow as utcnow

__all__ = ["CrossCountryCustomerSession"]


class CrossCountryCustomerSession(Base):
    __tablename__ = 'cross_country_customer_sessions'
    __table_args__ = {"schema": "customers"}
    uuid = Column(GUID(), default=uuid4, unique=True, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_deleted = Column(Boolean, default=False, server_default='false', nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(Integer, nullable=True)
    created_by = Column(Integer, nullable=True, index=True)
    updated_by = Column(Integer, nullable=True, index=True)
    __table_args__ = (Index('ix_cross_country_user', 'user_id'), {'schema': 'customers'})
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    source_country_code = Column(String(2), nullable=False)
    target_country_code = Column(String(2), nullable=False)
    session_data = Column(Text, nullable=True)
    conversion = Column(Boolean, default=False)
    order_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    user = relationship('User', primaryjoin='foreign(CrossCountryCustomerSession.user_id) == User.id')
    order = relationship('Order', primaryjoin='foreign(CrossCountryCustomerSession.order_id) == Order.id')
