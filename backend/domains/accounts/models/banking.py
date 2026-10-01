"""Banking models owned by the accounts domain.

``SupplierBankAccount`` and ``LogisticsPartnerBankAccount`` were relocated here
from ``governance.models.admin`` (the refactor shuffle). Per architecture Law 6
they live in the ``accounts`` schema. ``governance.ports`` and
``suppliers.models`` continue to re-export them so existing import sites are
unchanged.
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.sql import func

from infrastructure.database.base import Base


class SupplierBankAccount(Base):
    __tablename__ = "supplier_bank_accounts"
    __table_args__ = ({"schema": "accounts"},)

    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=False, index=True)
    account_number = Column(String(255), nullable=True)
    bank_name = Column(String(255), nullable=False)
    beneficiary_name = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    iban = Column(String(255), nullable=True)
    swift_code = Column(String(255), nullable=True)
    routing_number = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=True)
    bank_country = Column(String(3), nullable=True)
    verification_status = Column(String(255), default="pending")
    verification_note = Column(Text, nullable=True)
    provider = Column(String(255), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_status = Column(String(255), nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default="false", nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)


class LogisticsPartnerBankAccount(Base):
    __tablename__ = "logistics_partner_bank_accounts"
    __table_args__ = ({"schema": "accounts"},)

    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(Integer, ForeignKey("logistics.logistics_partners.id", ondelete="SET NULL"), nullable=False, index=True)
    account_number = Column(String(255), nullable=True)
    bank_name = Column(String(255), nullable=False)
    beneficiary_name = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    iban = Column(String(255), nullable=True)
    swift_code = Column(String(255), nullable=True)
    routing_number = Column(String(255), nullable=True)
    currency = Column(String(3), nullable=True)
    bank_country = Column(String(3), nullable=True)
    verification_status = Column(String(255), default="pending")
    verification_note = Column(Text, nullable=True)
    provider = Column(String(255), nullable=True)
    provider_recipient_id = Column(String(255), nullable=True)
    provider_status = Column(String(255), nullable=True)
    provider_last_synced_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by_id = Column(Integer, ForeignKey("accounts.users.id", ondelete="SET NULL"), nullable=True, index=True)
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False, server_default="false", nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
    country_code = Column(String(2), nullable=True, index=True)
