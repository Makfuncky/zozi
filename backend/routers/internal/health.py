"""
Health Check Endpoints for Zozi Platform
Provides comprehensive health status for monitoring and load balancers.
"""
import structlog
from fastapi import APIRouter

from data.services_core_health_service import (
    check_database,
    check_readiness,
    check_dependencies,
)

logger = structlog.get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "zozi-backend"}


@router.get("/health/db")
async def database_health():
    """Check database connectivity."""
    result = check_database()
    return {"status": result["status"], "database": result["status"]}


@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes/deployment readiness."""
    return check_readiness()


@router.get("/health/deps")
async def deps_health():
    """Comprehensive dependency health: DB, Redis, background jobs."""
    return check_dependencies()
