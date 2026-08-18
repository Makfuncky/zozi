"""Auto-migrated service logic from routers/incident.py."""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import Depends

from sqlalchemy.orm import Session

from domains.governance.services.auth_controller_service import get_current_user

from infrastructure.database.database import get_db

from domains.governance.models.incident import IncidentWarRoom







from domains.governance.services.admin_security_operations_service import close_incident






















from domains.governance.services.admin_security_operations_service import add_action_item














from domains.governance.services.admin_security_operations_service import get_war_room













