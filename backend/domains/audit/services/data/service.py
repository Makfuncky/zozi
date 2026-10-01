"""DEPRECATED: Moved to backend/domains/audit/services/logs/."""
import warnings
warnings.warn("This module has been moved to backend.domains.audit.services.logs", DeprecationWarning, stacklevel=2)
from domains.audit.services.logs.audit_service import *  # noqa: F401,F403
from domains.audit.services.logs.audit_query_service import *  # noqa: F401,F403
from domains.audit.services.logs.audit_trail_service import *  # noqa: F401,F403
from domains.audit.services.logs.user_activity_tracker import *  # noqa: F401,F403
