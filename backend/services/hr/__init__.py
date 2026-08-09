"""HR service layer.

Service modules under this package own all HR database access so that routers
only delegate (architecture circuit: routers -> services -> DB).
"""
import structlog
logger = structlog.get_logger(__name__)
