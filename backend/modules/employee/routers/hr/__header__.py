"""Employee hr router — consolidated from 10 source files."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body, status

from infrastructure.utils.pagination import paginated_response

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/api/v1/employee/hr", tags=["employee", "hr"])

