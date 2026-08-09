"""Audit domain package.

Holds audit-related *domain* services (e.g. ``audit_trail_service``,
``worm_audit``). The canonical cross-cutting audit primitives
(``AuditAction``, ``audit_log``) live in ``utils.audit`` and are imported
directly from there — this package does not re-export them.
"""
import structlog
logger = structlog.get_logger(__name__)
