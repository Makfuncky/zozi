"""
Health Check Endpoints for Zozi Platform
Provides comprehensive health status for monitoring and load balancers.
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.orm import Session
from db.database import get_db
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "zozi-backend"}

@router.get("/health/db")
async def database_health(db: Session = Depends(get_db)):
    """Check database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@router.get("/health/ready")
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness check for Kubernetes/deployment readiness."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not ready", "error": str(e)}

@router.get("/health/deps")
async def deps_health(db: Session = Depends(get_db)):
    """Comprehensive dependency health: DB, Redis, background jobs."""
    results = {"status": "healthy", "dependencies": {}}

    # Database
    try:
        db.execute(text("SELECT 1"))
        results["dependencies"]["database"] = {"status": "healthy"}
    except Exception as e:
        results["status"] = "unhealthy"
        results["dependencies"]["database"] = {"status": "unhealthy", "error": str(e)}

    # Redis
    try:
        from utils.config import settings
        import redis as redis_lib
        r = redis_lib.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        results["dependencies"]["redis"] = {"status": "healthy"}
    except Exception as e:
        results["status"] = "unhealthy"
        results["dependencies"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Background jobs
    try:
        from utils.background_jobs import job_stats
        stats = job_stats()
        bg_status = "healthy" if stats.get("running", 0) < (stats.get("max_concurrent", 10) * 2) else "degraded"
        results["dependencies"]["background_jobs"] = {"status": bg_status, **stats}
    except Exception as e:
        results["dependencies"]["background_jobs"] = {"status": "unknown", "error": str(e)}

    return results

