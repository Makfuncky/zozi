"""
Escalation SLA Telemetry Service
Auto-escalates unread urgent messages to higher roles after defined SLA windows.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from models.core import EscalationSLARule, EscalationSLALog
from utils.datetime_utils import utcnow as _utcnow

logger = logging.getLogger("zozi.escalation_sla")


class EscalationSLAService:
    def __init__(self, db: Session):
        self.db = db

    DEFAULT_RULES = [
        {"priority": "urgent", "escalate_after_minutes": 15, "escalate_to_role": "country_head", "notify_via": "sms,email"},
        {"priority": "high", "escalate_after_minutes": 30, "escalate_to_role": "country_head", "notify_via": "email"},
        {"priority": "normal", "escalate_after_minutes": 120, "escalate_to_role": "country_manager", "notify_via": "email"},
    ]

    def ensure_default_rules(self):
        existing = self.db.query(EscalationSLARule).count()
        if existing == 0:
            for rule in self.DEFAULT_RULES:
                self.db.add(EscalationSLARule(**rule))
            self.db.commit()

    def get_rule_for_priority(self, priority: str) -> Optional[EscalationSLARule]:
        return self.db.query(EscalationSLARule).filter(
            EscalationSLARule.priority == priority,
            EscalationSLARule.is_active == True,
        ).first()

    def track_message(
        self,
        message_id: int,
        message_type: str,
        recipient_id: int,
        priority: str,
    ) -> dict:
        rule = self.get_rule_for_priority(priority)
        if not rule:
            return {"escalation": False, "reason": "no_rule_for_priority"}

        log = EscalationSLALog(
            message_id=message_id,
            message_type=message_type,
            original_recipient_id=recipient_id,
            priority=priority,
            escalate_after_minutes=rule.escalate_after_minutes,
            escalate_to_role=rule.escalate_to_role,
            status="pending",
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)

        return {
            "tracking_id": log.id,
            "escalation_sla_minutes": rule.escalate_after_minutes,
            "escalate_to_role": rule.escalate_to_role,
        }

    def check_and_escalate(self) -> List[dict]:
        self.ensure_default_rules()
        now = _utcnow()
        escalated = []

        pending_logs = self.db.query(EscalationSLALog).filter(
            EscalationSLALog.status == "pending",
        ).all()

        for log in pending_logs:
            rule = self.get_rule_for_priority(log.priority)
            if not rule:
                continue

            elapsed = (now - log.created_at).total_seconds() / 60
            log.elapsed_minutes = int(elapsed)

            if elapsed >= rule.escalate_after_minutes:
                log.status = "escalated"
                log.escalated_at = now
                log.escalated_to_role = rule.escalate_to_role
                self.db.commit()

                escalated.append({
                    "tracking_id": log.id,
                    "message_id": log.message_id,
                    "original_recipient_id": log.original_recipient_id,
                    "escalated_to_role": rule.escalate_to_role,
                    "escalated_at": now.isoformat(),
                    "notify_via": rule.notify_via,
                })
                logger.info(
                    f"Escalated message {log.message_id} to {rule.escalate_to_role} "
                    f"after {int(elapsed)} min ({log.priority})"
                )

        return escalated

    def acknowledge_escalation(self, tracking_id: int) -> dict:
        log = self.db.query(EscalationSLALog).filter(
            EscalationSLALog.id == tracking_id,
            EscalationSLALog.status == "escalated",
        ).first()
        if not log:
            return {"error": "No active escalation found"}

        log.status = "acknowledged"
        log.acknowledged_at = _utcnow()
        self.db.commit()

        return {
            "tracking_id": tracking_id,
            "status": "acknowledged",
            "acknowledged_at": log.acknowledged_at.isoformat(),
        }


def get_escalation_sla_service(db: Session) -> EscalationSLAService:
    return EscalationSLAService(db)
