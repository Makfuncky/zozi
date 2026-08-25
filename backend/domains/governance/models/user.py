"""User model for governance domain."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, func
from sqlalchemy.orm import relationship

from . import Base
from infrastructure.utils.datetime_utils import utcnow as _utcnow


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(String(50), default="customer")
    country_code = Column(String(2))
    is_active = Column(Boolean, default=True)
    staff_country_codes = Column(Text)  # JSON array of country codes
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


class UserLoginHistory(Base):
    __tablename__ = "user_login_history"
    __table_args__ = {"schema": "governance"}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("governance.users.id"), nullable=False)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)
