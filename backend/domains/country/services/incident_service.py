"""Auto-migrated service logic from routers/incident.py."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends

from sqlalchemy.orm import Session

from rbac.routers.auth_controller import get_current_user

from infrastructure.database.database import get_db

from _legacy.models import IncidentWarRoom

from services.security.incident_service import get_incident_service





from services.admin.admin_security_operations_service import create_incident  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

from services.admin.admin_security_operations_service import close_incident  # [MIGRATION COMPAT] re-export relocated symbol






















from services.admin.admin_security_operations_service import add_action_item  # [MIGRATION COMPAT] re-export relocated symbol














from services.admin.admin_security_operations_service import get_war_room  # [MIGRATION COMPAT] re-export relocated symbol












from services.admin.admin_security_operations_service import create_incident  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

