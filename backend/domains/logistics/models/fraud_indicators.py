"""Logistics fraud indicator model (moved from security domain per Law 3)."""
from __future__ import annotations

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from . import Base

__all__ = ["LogisticsFraudIndicator"]


