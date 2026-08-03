"""Health-check service.

Isolates DB / Redis / background-job probes from the router layer so routers no
longer hold a database session directly (clears W1). Each probe owns its session
via ``data.db.get_db_context``.
"""
import structlog
from sqlalchemy import text

logger = structlog.get_logger(__name__)


def check_database() -> dict:
    """Verify the database is reachable."""
    from data.db import get_db_context

    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:  # pragma: no cover - depends on live DB
        logger.error("Database health check failed", error=str(e))
        return {"status": "unhealthy", "error": str(e)}


def check_readiness() -> dict:
    """Readiness probe for deployment orchestrators."""
    from data.db import get_db_context

    try:
        with get_db_context() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:  # pragma: no cover - depends on live DB
        logger.error("Readiness check failed", error=str(e))
        return {"status": "not ready", "error": str(e)}


def check_dependencies() -> dict:
    """Comprehensive dependency health: database, Redis, background jobs."""
    results: dict = {"status": "healthy", "dependencies": {}}

    results["dependencies"]["database"] = check_database()
    if results["dependencies"]["database"]["status"] != "healthy":
        results["status"] = "unhealthy"

    # Redis
    try:
        import redis as redis_lib

        from utils.config import settings

        r = redis_lib.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        results["dependencies"]["redis"] = {"status": "healthy"}
    except Exception as e:  # pragma: no cover - depends on live Redis
        results["status"] = "unhealthy"
        results["dependencies"]["redis"] = {"status": "unhealthy", "error": str(e)}

    # Background jobs
    try:
        from utils.background_jobs import job_stats

        stats = job_stats()
        bg_status = (
            "healthy"
            if stats.get("running", 0) < (stats.get("max_concurrent", 10) * 2)
            else "degraded"
        )
        results["dependencies"]["background_jobs"] = {"status": bg_status, **stats}
    except Exception as e:  # pragma: no cover - depends on live job runner
        results["dependencies"]["background_jobs"] = {"status": "unknown", "error": str(e)}

    return results
