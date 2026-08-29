"""Supplier fraud indicator model (moved from security domain per Law 3)."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from . import Base

__all__ = ["SupplierFraudIndicator"]


class SupplierFraudIndicator(Base):
    __tablename__ = "supplier_fraud_indicators"
    __table_args__ = {"schema": "suppliers"}
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete='SET NULL'), nullable=False)
    indicator_type = Column(String(50), nullable=False)
    value = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
