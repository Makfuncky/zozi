"""Risk Management Controller for Fraud Detection and Telemetry."""
from __future__ import annotations
from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from services.security.risk_service import (
    detect_ghost_employees,
    detect_impossible_travel,
    update_flight_risk_score,
    get_team_health_radar,
    get_audit_timeline,
)
