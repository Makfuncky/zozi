"""Promotions router for employee module — thin delegating to domain services."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from infrastructure.database.database import get_db
from infrastructure.security.dependencies import require_employee
from rbac.dependencies import require_feature

router = APIRouter(prefix="/api/v1/employee/promotions", tags=["employee", "promotions"])

# TODO: Add endpoints as domain services are implemented
