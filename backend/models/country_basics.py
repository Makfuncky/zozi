from __future__ import annotations


from sqlalchemy import Boolean, Column, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship

from utils.datetime_utils import utcnow as _utcnow

from . import Base

__all__ = ["CountryBasics"]


class CountryBasics(Base):
    __tablename__ = "country_basics"
    __table_args__ = (
        Index("ix_country_basics_code", "code", unique=True), {"schema": "country"}
    )
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(3), unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    currency = Column(String(3), default="USD")
    currency_symbol = Column(String(10), nullable=True)
    phone_code = Column(String(10), nullable=True)
    language = Column(String(10), default="en")
    timezone = Column(String(60), nullable=True)
    date_format = Column(String(20), default="DD/MM/YYYY")
    status = Column(String(20), default="active")
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)
    official_name = Column(String(200), nullable=True)
    alpha3 = Column(String(3), nullable=True)
    flag_url = Column(String(500), nullable=True)
    currency_name = Column(String(50), nullable=True)
    exchange_rate_to_usd = Column(Numeric(12, 6), nullable=True)
    capital = Column(String(100), nullable=True)
    region = Column(String(60), nullable=True)
    subregion = Column(String(60), nullable=True)
    population = Column(Integer, nullable=True)
    internet_penetration_pct = Column(Numeric(5, 2), nullable=True)
    gdp_per_capita_usd = Column(Numeric(12, 2), nullable=True)
    urbanization_pct = Column(Numeric(5, 2), nullable=True)
    mobile_subs_per_100 = Column(Numeric(5, 2), nullable=True)
    public_holidays_json = Column(Text, nullable=True)
    macro_indicators_json = Column(Text, nullable=True)

    country = relationship("CountryConfig", back_populates="basics", foreign_keys="CountryConfig.basics_id")