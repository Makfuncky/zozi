"""controllers.security.risk_controller controller.

Business logic is delegated to services.security.risk_service (routers -> controllers -> services)."""

from services.security.risk_service import (
    detect_ghost_employees, detect_impossible_travel, get_audit_timeline, get_team_health_radar, update_flight_risk_score
)

__all__ = [
    "detect_ghost_employees", "detect_impossible_travel", "get_audit_timeline", "get_team_health_radar", "update_flight_risk_score"
]
