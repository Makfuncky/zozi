"""Shared dependency factories for the fraud / threat-detection engines.

Promoted from the security-detection routers so the auto-router generator can
wire ``get_fraud_engine`` / ``get_threat_updater`` as controller dependencies.
"""
from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from infrastructure.database.database import get_db
from domains.security.services.fraud.fraud_detection_service import FraudScoringEngine
from domains.security.services.fraud.fraud_detection_service import ThreatFeedUpdater
from infrastructure.valkey.client import get_valkey


def get_fraud_engine(db: Session = Depends(get_db), valkey=Depends(get_valkey)):
    """Return a configured FraudScoringEngine instance."""
    return FraudScoringEngine(db=db, valkey=valkey)


def get_threat_updater(db: Session = Depends(get_db), valkey=Depends(get_valkey)):
    """Return a configured ThreatFeedUpdater instance."""
    return ThreatFeedUpdater(db=db, valkey=valkey)
