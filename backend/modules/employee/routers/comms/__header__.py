"""Employee comms router — consolidated from 23 source files."""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from infrastructure.utils.pagination import paginated_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/employee/comms", tags=["employee", "comms"])

