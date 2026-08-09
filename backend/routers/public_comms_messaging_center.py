"""Email Gateway Router"""
from routers.public_email_controller_access import router as email_router
import structlog
logger = structlog.get_logger(__name__)

router = email_router

