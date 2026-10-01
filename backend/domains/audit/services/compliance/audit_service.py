"""DEPRECATED: Moved to backend/domains/audit/services/logs/."""
import warnings
warnings.warn("This module has been moved to backend.domains.audit.services.logs", DeprecationWarning, stacklevel=2)
from domains.audit.services.logs.audit_service import *  # noqa: F401,F403

