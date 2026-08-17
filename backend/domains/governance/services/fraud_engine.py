"""Shared dependency factories for the fraud / threat-detection engines.

Promoted from the security-detection routers so the auto-router generator can
wire ``get_fraud_engine`` / ``get_threat_updater`` as controller dependencies.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from services.security.fraud_detection_service import (
    FraudScoringEngine,
    ThreatFeedUpdater,
)
from infrastructure.utils.redis_client import get_redis





from services.admin.admin_security_detection_service import get_fraud_engine  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)

# --- auto-wiring re-exports (added by fix_modules) ---
from services.admin.admin_security_detection_service import get_threat_updater






from services.admin.admin_security_detection_service import get_fraud_engine  # [MIGRATION COMPAT] re-export relocated symbol (see ARCHITECTURE_MIGRATION_REPORT.md)


