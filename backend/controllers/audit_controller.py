"""
Audit Controller — centralised logging of security-sensitive and business-critical events.

The canonical AuditAction + audit_log live in utils/audit_log.py.
This module re-exports them for backward compatibility so that all existing
``from controllers.audit_controller import audit_log`` imports keep working.

Usage (anywhere in the backend):
    from controllers.audit_controller import audit_log
    from utils.ip_utils import get_request_ip

    audit_log(
        db=db,
        action="LOGIN_SUCCESS",
        user_id=user.id,
        username=user.username,
        user_role=user.role,
        ip_address=get_request_ip(request),
        user_agent=request.headers.get("user-agent"),
        status="success",
        details={"method": "email"},
    )
"""

# Re-export from the shared module (single source of truth)
from utils.audit_log import AuditAction, audit_log, get_audit_logs, get_unique_actions  # noqa: F401
