from __future__ import annotations

"""Chart of Categories (CoC) - 7-Layer Taxonomy System.

Layer 1: Department (Electronics, Fashion)
Layer 2: Category (Computers, Men's Clothing)
Layer 3: Sub-Category (Laptops, Shirts)
Layer 4: Product Type (Gaming Laptop, Polo Shirt)
Layer 5: Brand / IP (ASUS ROG, Nike)
Layer 6: Key Spec / Variant (RTX 4060 16GB, Red Cotton XL)
Layer 7: SKU / Leaf (actual sellable product variant)

Levels 1-3 are strict relational nodes in this table.
Levels 4-7 are handled via product_types and attributes.
"""

from sqlalchemy import (
    Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    UniqueConstraint, Index,
    func,

)
from sqlalchemy.orm import relationship

from infrastructure.database.base import Base


class ChartOfCategory(Base):
    """Levels 1-3 of the Chart of Categories (strict relational nodes)."""

    __tablename__ = "chart_of_categories"
    __table_args__ = (
        UniqueConstraint("parent_id", "slug", name="uq_coc_parent_slug"),
        Index("ix_coc_parent_id", "parent_id"),
        Index("ix_coc_level", "level"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey("catalog.chart_of_categories.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    level = Column(Integer, nullable=False)  # 1, 2, or 3
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)

    # Commission group link
    commission_group_id = Column(Integer, ForeignKey("catalog.commission_groups.id", ondelete="SET NULL"), nullable=True, index=True)

    # Materialized path for fast tree queries
    path = Column(String(500), nullable=True, index=True)
    depth = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    parent = relationship("ChartOfCategory", remote_side=[id], back_populates="children")
    children = relationship("ChartOfCategory", back_populates="parent", cascade="all, delete-orphan")
    product_types = relationship("ProductType", back_populates="coc_category", cascade="all, delete-orphan")
    commission_group = relationship("CommissionGroup", back_populates="categories")

    def __repr__(self) -> str:
        return f"<CoC(L{self.level}): {self.name}>"


class ProductType(Base):
    """Level 4: Product Type - links to Level 3 CoC.

    Examples: "Gaming Laptop", "Polo Shirt", "In-Game Currency"
    """

    __tablename__ = "product_types"
    __table_args__ = (
        UniqueConstraint("coc_category_id", "slug", name="uq_pt_coc_slug"),
        Index("ix_pt_coc_category_id", "coc_category_id"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    coc_category_id = Column(Integer, ForeignKey("catalog.chart_of_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Attribute schema for this product type (defines Levels 5-6)
    attribute_schema = Column(Text, nullable=True)  # JSON: [{"key": "brand", "label": "Brand", "type": "select"}]

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    coc_category = relationship("ChartOfCategory", back_populates="product_types")
    attributes = relationship("CategoryAttribute", back_populates="product_type", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<ProductType: {self.name}>"


class CategoryAttribute(Base):
    """Levels 5-6: Dynamic attributes for product types.

    Level 5: Brand / IP (ASUS ROG, Nike, PUBG Mobile)
    Level 6: Key Spec / Variant (RTX 4060 16GB, Red Cotton XL)
    """

    __tablename__ = "category_attributes"
    __table_args__ = (
        UniqueConstraint("product_type_id", "key", name="uq_ca_pt_key"),
        Index("ix_ca_product_type_id", "product_type_id"),
        Index("ix_ca_layer", "layer"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    product_type_id = Column(Integer, ForeignKey("catalog.product_types.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key = Column(String(50), nullable=False)
    layer = Column(Integer, nullable=False)  # 5 or 6
    value_type = Column(String(20), default="select")  # select, text, number, boolean
    options = Column(Text, nullable=True)  # JSON array for select type
    is_required = Column(Boolean, default=False)
    is_filterable = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    product_type = relationship("ProductType", back_populates="attributes")
    values = relationship("CategoryAttributeValue", back_populates="attribute", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Attribute L{self.layer}: {self.name}>"


class CategoryAttributeValue(Base):
    """Pre-defined values for category attributes (e.g., list of brands)."""

    __tablename__ = "category_attribute_values"
    __table_args__ = (
        UniqueConstraint("attribute_id", "value", name="uq_cav_attr_value"),
        Index("ix_cav_attribute_id", "attribute_id"),
        {"schema": "catalog"},
    )

    id = Column(Integer, primary_key=True)
    attribute_id = Column(Integer, ForeignKey("catalog.category_attributes.id", ondelete="CASCADE"), nullable=False, index=True)
    value = Column(String(200), nullable=False)
    label = Column(String(200), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)

    # Audit columns (Law 23/229)
    country_code = Column(String(2), nullable=True, index=True)
    is_deleted = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    version = Column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    attribute = relationship("CategoryAttribute", back_populates="values")

    def __repr__(self) -> str:
        return f"<AttrValue: {self.value}>"
