"""Jobs layer.

Operational modules (background task runners, seeding, and tool servers) that
sit at circuit layer 4. They may call downward into services (4), providers (5),
models (6) and db (7) without violating the circuit direction.
"""
import structlog
logger = structlog.get_logger(__name__)
