"""governance domain — legal contract template model previously housed under country.

This table was originally defined in ``domains/country/models/country_control.py``.
It is a governance/legal artefact and has been relocated here.

The ``__tablename__`` is preserved unchanged. The schema has been corrected to
``governance`` (was ``country``) to comply with Law 6 (schema discipline).
"""
from __future__ import annotations
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import relationship
from . import Base

__all__ = ["LegalContractTemplate"]


class LegalContractTemplate(Base):
    __tablename__ = "legal_contract_templates"
    __table_args__ = (
        UniqueConstraint("country_code", "template_type", name="uq_lct_country_type"),
        Index("ix_lct_type", "template_type"),
        {"schema": "governance"},
    )

    id = Column(Integer, primary_key=True, index=True)
    country_code = Column(String(2), ForeignKey("country.country_configs.code", ondelete="SET NULL"), nullable=False, index=True)
    template_type = Column(String(50), nullable=False)
    version = Column(String(20), default="1.0")
    content = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    country = relationship("CountryConfig")
