"""Command Center Router"""
from routers.public_analytics_command_center_api import router as command_router
import structlog
logger = structlog.get_logger(__name__)

router = command_router

