"""Global error handler for Zozi Platform."""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handling."""

    async def handle_exception(self, request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )


def create_error_handler():
    """Create an ErrorHandler instance."""
    return ErrorHandler()


async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for FastAPI."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )
