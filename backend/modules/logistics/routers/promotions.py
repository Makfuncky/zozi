"""Promotions router for logistics module — thin delegating to domain services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_logistics
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/logistics/promotions", tags=["logistics", "promotions"])

# TODO: Add endpoints as domain services are implemented
