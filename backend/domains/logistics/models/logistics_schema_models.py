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
# ``domains.accounts.models.core`` God-module (A3 / RESOLVER §26 ACC-01).
# ``domains.accounts.models.core`` keeps re-exports so legacy imports resolve.

__all__ = ["CityDistanceMatrix"]


class CityDistanceMatrix(Base):
    __tablename__ = "city_distance_matrix"
    __table_args__ = ({"schema": "logistics"},)
    id = Column(Integer, primary_key=True, index=True)
    origin_country_code = Column(String(10), nullable=False)
    origin_city_name = Column(String, nullable=False)
    destination_country_code = Column(String(10), nullable=False)
    destination_city_name = Column(String, nullable=False)
    distance_km = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    updated_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=True)
    created_at = Column(DateTime, default=_utcnow)
