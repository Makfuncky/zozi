from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow

# Canonical home for ``logistics``-schema tables that lived in the old
# ``domains.governance.models.core`` God-module (A3 / RESOLVER §26 ACC-01).
# ``domains.governance.models.core`` keeps re-exports so legacy imports resolve.

__all__ = ["CityDistanceMatrix"]


class CityDistanceMatrix(Base):
    __tablename__ = "city_distance_matrices"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    origin_country_code = Column(String(2), nullable=False)
    origin_city_name = Column(String, nullable=False)
    destination_country_code = Column(String(2), nullable=False)
    destination_city_name = Column(String, nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    updated_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code"), nullable=True, index=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow, nullable=True)
