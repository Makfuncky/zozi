"""Supplier suppliers router — shared router definition."""
import logging
from fastapi import APIRouter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/supplier/suppliers", tags=["supplier", "suppliers"])
