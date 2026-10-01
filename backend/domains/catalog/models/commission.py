from __future__ import annotations

"""Waterfall Commission Matrix Models.

Commission is calculated using a waterfall approach:
1. Check SKU exact match (Level 7)
2. Check Supplier + Brand (Level 5)
3. Check Supplier + Product Type (Level 4)
4. Check Supplier + Sub-Category (Level 3)
5. Check Commission Group base rate
6. Check Global default rate

First match wins.
"""

from sqlalchemy import (
    Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text,
    UniqueConstraint, Index,
    func,

)
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base


class CommissionGroup(Base):
    """Groups of categories that share the same base commission rate.

    Instead of setting commission for 1000+ categories individually,
    admins group them into 10-20 commission groups.
    """

    __tablename__ = "commission_groups"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_cg_slug"),
        Index("ix_cg_is_active", "is_active"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    base_rate = Column(Numeric(5, 2), nullable=False, default=10.00)  # percentage
    max_commission_amount = Column(Numeric(12, 2), nullable=True)  # cap per transaction
    is_active = Column(Boolean, default=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    categories = relationship("ChartOfCategory", back_populates="commission_group")
    rules = relationship("CommissionRule", back_populates="commission_group", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CommissionGroup: {self.name} ({self.base_rate}%)>"


class CommissionProfile(Base):
    """Supplier commission profile - a collection of commission rules.

    Each supplier has one or more profiles. A profile contains
    multiple rules that override the base commission group rates.
    """

    __tablename__ = "commission_profiles"
    __table_args__ = (
        UniqueConstraint("supplier_id", "slug", name="uq_cp_supplier_slug"),
        Index("ix_cp_supplier_id", "supplier_id"),
        Index("ix_cp_is_active", "is_active"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    supplier_id = Column(Integer, nullable=False, index=True)  # Links to supplier table
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    is_default = Column(Boolean, default=False)  # Default profile for this supplier
    is_active = Column(Boolean, default=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    rules = relationship("CommissionRule", back_populates="profile", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<CommissionProfile: {self.name}>"


class CommissionRule(Base):
    """Individual commission rule within a profile.

    Rules are evaluated by priority (lowest first). First match wins.
    """
    __tablename__ = "commission_rules"
    __table_args__ = (
        Index("ix_cr_profile_id", "profile_id"),
        Index("ix_cr_priority", "priority"),
        Index("ix_cr_is_active", "is_active"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    profile_id = Column(Integer, ForeignKey("catalog.commission_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    commission_group_id = Column(Integer, ForeignKey("catalog.commission_groups.id", ondelete="SET NULL"), nullable=True, index=True)

    # Rule matching criteria
    name = Column(String(200), nullable=False)
    coc_node_id = Column(Integer, ForeignKey("catalog.chart_of_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    product_type_id = Column(Integer, ForeignKey("catalog.product_types.id", ondelete="SET NULL"), nullable=True, index=True)
    brand = Column(String(100), nullable=True)  # Level 5 override
    attribute_key = Column(String(50), nullable=True)  # Level 6 attribute key
    attribute_value = Column(String(200), nullable=True)  # Level 6 attribute value

    # Commission rate
    rate = Column(Numeric(5, 2), nullable=False)  # percentage
    max_commission_amount = Column(Numeric(12, 2), nullable=True)  # cap per transaction

    # Rule priority (lower = higher priority, evaluated first)
    priority = Column(Integer, default=100)

    # Effective date range
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)

    is_active = Column(Boolean, default=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    profile = relationship("CommissionProfile", back_populates="rules")
    commission_group = relationship("CommissionGroup", back_populates="rules")

    def __repr__(self) -> str:
        return f"<CommissionRule: {self.name} ({self.rate}%)>"


class CommissionTransaction(Base):
    """Record of commission calculated for each transaction."""

    __tablename__ = "commission_transactions"
    __table_args__ = (
        Index("ix_ct_order_id", "order_id"),
        Index("ix_ct_supplier_id", "supplier_id"),
        Index("ix_ct_calculated_at", "calculated_at"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False, index=True)
    supplier_id = Column(Integer, nullable=False, index=True)
    product_id = Column(Integer, nullable=False)

    # Commission details
    gross_amount = Column(Numeric(12, 2), nullable=False)
    commission_rate = Column(Numeric(5, 2), nullable=False)
    commission_amount = Column(Numeric(12, 2), nullable=False)
    net_amount = Column(Numeric(12, 2), nullable=False)

    # Rule that was applied
    rule_id = Column(Integer, ForeignKey("catalog.commission_rules.id", ondelete="SET NULL"), nullable=True, index=True)
    rule_name = Column(String(200), nullable=True)

    # CoC path at time of transaction
    coc_path = Column(String(500), nullable=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    calculated_at = Column(DateTime, server_default=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    def __repr__(self) -> str:
        return f"<CommissionTx: order={self.order_id} rate={self.commission_rate}%>"
