"""PromotionLedgerEntry model for promotions domain."""
from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func

from infrastructure.database.base import Base


class PromotionLedgerEntry(Base):
    """Audit ledger for promotion discount applications."""
    __tablename__ = "promotion_ledger_entries"
    __table_args__ = {"schema": "promotions"}
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(Integer, nullable=True)
    order_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True, index=True)
    promotion_type = Column(String(50), nullable=True)
    promotion_code = Column(String(100), nullable=True)
    tier_id = Column(Integer, nullable=True)
    amount = Column(Numeric(12, 2), nullable=False)
    entry_type = Column(String(255), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False)
    points_awarded = Column(Integer, default=0)
    points_redeemed = Column(Integer, default=0)
    stacking_flag = Column(Integer, default=0)
    source = Column(String(50), nullable=True)
    metadata_json = Column(String(500), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
