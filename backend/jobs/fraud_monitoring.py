from __future__ import annotations

import logging


from infrastructure.database.database import SessionLocal
from domains.governance.services.fraud_detection import FraudDetectionService
from domains.comms.services.notification_service import NotificationService
import structlog
logger = structlog.get_logger(__name__)

logger = logging.getLogger(__name__)


def run_ghost_employee_detection():
    """Nightly task to detect and flag ghost employees."""
    db = SessionLocal()
    try:
        fraud_service = FraudDetectionService(db)
        notification_service = NotificationService(db)
        
        ghost_employees = fraud_service.detect_ghost_employees()
        
        for user_id in ghost_employees:
            fraud_service.freeze_payroll_for_ghost(user_id)
            notification_service.send_alert(
                "ghost_employee",
                {"user_id": user_id, "action": "payroll_frozen"},
                priority="high",
            )
        
        logger.info(f"Ghost employee detection complete: {len(ghost_employees)} flagged")
    finally:
        db.close()


def run_anomaly_detection():
    """Detect anomalous behavior patterns."""
    db = SessionLocal()
    try:
        fraud_service = FraudDetectionService(db)
        notification_service = NotificationService(db)
        
        anomalies = fraud_service.detect_anomalies()
        
        for anomaly in anomalies:
            notification_service.send_alert(
                "behavioral_anomaly",
                anomaly,
                priority=anomaly.get("severity", "medium"),
            )
        
        logger.info(f"Anomaly detection complete: {len(anomalies)} anomalies found")
    finally:
        db.close()

