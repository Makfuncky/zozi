"""Shared dependency factories for the fraud / threat-detection engines.

Promoted from the security-detection routers so the auto-router generator can
wire ``get_fraud_engine`` / ``get_threat_updater`` as controller dependencies.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.governance.services.fraud.fraud_detection_service import FraudScoringEngine
from domains.governance.services.fraud.fraud_detection_service import ThreatFeedUpdater
from infrastructure.utils.redis_client import get_redis






# --- auto-wiring re-exports (added by fix_modules) ---
from domains.governance.services.security.admin_security_detection_service import get_threat_updater








