"""Loyalty points models for promotions domain."""
from __future__ import annotations

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from infrastructure.database.base import Base


class UserPoints(Base):
    """User loyalty points balance."""
    __tablename__ = "user_points"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False, unique=True)
    balance = Column(Integer, default=0, nullable=False)
    lifetime_earned = Column(Integer, default=0, nullable=False)
    lifetime_redeemed = Column(Integer, default=0, nullable=False)
    loyalty_tier = Column(String(20), default="bronze", nullable=False)
    points_expire_at = Column(DateTime, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)


class PointsTransaction(Base):
    """Audit trail for points transactions."""
    __tablename__ = "points_transactions"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="CASCADE"), nullable=False)
    points = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)
    order_id = Column(Integer, nullable=True)
    source_description = Column(String(255), nullable=True)
    balance_after = Column(Integer, nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
