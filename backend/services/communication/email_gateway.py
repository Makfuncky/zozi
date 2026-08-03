"""
Enterprise Email Gateway
Features: Role-Based Aliases, DLP, PII Redaction, Legal Templating
"""
import uuid
import json
import logging
import re
import hashlib
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Session

from data.models import User
from models.communication import Notification, InternalEmail, EmailFolder
from data.models_employee_models import Employee
from data.models_fraud import DLPViolation
from utils.email_service import send_email, get_email_sender_address, build_email_open_tracking_url


logger = logging.getLogger("zozi.email")


class DLPScanner:
    """Data Loss Prevention scanner for outbound emails."""
    
    PII_PATTERNS = {
        "national_id": r"\b\d{9}\b",
        "credit_card": r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b",
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "phone": r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "iban": r"\b[A-Z]{2}\d{2}[A-Z0-9]{4}\d{7}([A-Z0-9]?){0,16}\b",
        "api_key": r"(api_key|apikey|secret|password)\s*[:=]\s*['\"]?[a-zA-Z0-9_-]{20,}['\"]?",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "passport": r"\b[A-Z]\d{8}\b",
    }
    
    @classmethod
    def scan_content(cls, content: str) -> Dict[str, Any]:
        """Scan content for PII and sensitive data."""
        findings = {}
        for pattern_name, pattern in cls.PII_PATTERNS.items():
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                findings[pattern_name] = len(matches)
        
        total_findings = sum(findings.values())
        if total_findings >= 3:
            risk_level = "high"
        elif total_findings >= 1:
            risk_level = "medium"
        else:
            risk_level = "none"
        
        return {
            "is_safe": total_findings == 0,
            "findings": findings,
            "risk_level": risk_level
        }
    
    @classmethod
    def redact_content(cls, content: str) -> str:
        """Redact sensitive data from content."""
        redacted = content
        for pattern_name, pattern in cls.PII_PATTERNS.items():
            redacted = re.sub(pattern, "[REDACTED]", redacted, flags=re.IGNORECASE)
        return redacted


class RoleBasedAliasManager:
    """Manages role-based email aliases."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_alias_for_role(self, role: str, country_code: str = None) -> str:
        """Get the email alias for a role."""
        return f"{role.lower()}.{country_code or 'global'}@zozi.com"
    
    def get_role_from_alias(self, alias: str) -> Optional[str]:
        """Extract role from alias."""
        match = re.match(r"^([a-z]+)\.", alias)
        return match.group(1) if match else None


class EmailGateway:
    def __init__(self, db: Session):
        self.db = db
        self.dlp_scanner = DLPScanner()
        self.alias_manager = RoleBasedAliasManager(db)
    
    def send_internal_email(self, to_user_ids: List[int], subject: str,
                            body: str, sender_id: int, in_reply_to: Optional[int] = None) -> dict:
        users = self.db.query(User).filter(User.id.in_(to_user_ids)).all()
        now = datetime.now(timezone.utc)
        thread_id = str(uuid.uuid4())

        # If replying to an existing email, inherit its thread_id
        if in_reply_to:
            parent = self.db.query(InternalEmail).filter(InternalEmail.id == in_reply_to).first()
            if parent:
                thread_id = parent.thread_id

        recipients_json = [{"user_id": uid, "type": "to"} for uid in to_user_ids]
        body_html = f"<p>{body.replace(chr(10), '</p><p>')}</p>" if body else ""
        email = InternalEmail(
            sender_id=sender_id,
            subject=subject,
            body_html=body_html,
            body_text=body,
            recipients=json.dumps(recipients_json, default=str),
            thread_id=thread_id,
            in_reply_to=in_reply_to,
            is_external=False,
            country_code=getattr(getattr(users[0], "employee_profile", None), "country_code", None) if users else None,
            created_at=now,
        )
        self.db.add(email)
        self.db.flush()

        for u in users:
            emp = None
            if hasattr(u, "employee_profile") and u.employee_profile is not None:
                emp = u.employee_profile
                if isinstance(emp, list):
                    emp = emp[0] if emp else None
            if not emp:
                emp = self.db.query(Employee).filter(Employee.user_id == u.id).first()
            if not emp:
                continue
            folder = (
                self.db.query(EmailFolder)
                .filter(EmailFolder.employee_id == emp.id, EmailFolder.name == "inbox")
                .first()
            )
            if not folder:
                folder = EmailFolder(employee_id=emp.id, name="inbox", folder_type="inbox", is_system=True)
                self.db.add(folder)
                self.db.flush()
            email.folder_id = folder.id

        self.db.commit()
        self.db.refresh(email)

        try:
            from services.employee_communication_service import _log_comm_event
            _log_comm_event(self.db, sender_id, to_user_ids[0] if to_user_ids else None, "email_sent", "internal_email", email.id)
        except Exception as exc:
            logger.debug("Activity log skipped: %s", exc)

        _enqueue_email_delivery(email.id, body_html, subject)

        return {
            "email_id": email.id,
            "thread_id": email.thread_id,
            "to": to_user_ids,
            "subject": subject,
            "body": body,
            "sender_id": sender_id,
            "sent_at": email.created_at.isoformat(),
            "status": "sent",
            "delivered_count": len(users),
            "total_count": len(to_user_ids),
        }
    
    def send_external_email(self, to_email: str, subject: str, body: str,
                            sender_id: int, template_id: Optional[str] = None) -> dict:
        dlp_result = self.dlp_scanner.scan_content(body)
        
        if not dlp_result["is_safe"]:
            logger.warning(f"DLP blocked email to {to_email}. Findings: {dlp_result['findings']}")
            self._log_dlp_violation(sender_id, to_email, dlp_result, subject)
            return {
                "email_id": f"blocked_{datetime.now(timezone.utc).timestamp()}",
                "to": to_email,
                "subject": subject,
                "status": "blocked",
                "reason": "DLP violation detected",
                "dlp_findings": dlp_result["findings"]
            }
        
        try:
            send_email(to_email, subject, body, purpose="external", from_address=get_email_sender_address("external"))
            return {
                "email_id": f"ext_email_{datetime.now(timezone.utc).timestamp()}",
                "to": to_email,
                "subject": subject,
                "body": body,
                "sender_id": sender_id,
                "template_id": template_id,
                "sent_at": datetime.now(timezone.utc).isoformat(),
                "status": "sent"
            }
        except Exception as e:
            logger.error(f"Failed to send external email to {to_email}: {e}")
            return {
                "email_id": f"ext_email_{datetime.now(timezone.utc).timestamp()}",
                "to": to_email,
                "subject": subject,
                "status": "failed",
                "error": str(e),
            }
    
    def send_from_alias(self, alias: str, to_email: str, subject: str, body: str,
                        sender_id: int) -> dict:
        """Send email from a role-based alias."""
        from_address = get_email_sender_address("external", alias)
        try:
            send_email(to_email, subject, body, purpose="external", from_address=from_address)
            return {
                "email_id": f"alias_email_{datetime.now(timezone.utc).timestamp()}",
                "from": alias,
                "to": to_email,
                "subject": subject,
                "status": "sent"
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def get_email_templates(self) -> List[dict]:
        return [
            {"id": "offer", "name": "Offer Letter", "type": "legal"},
            {"id": "contract", "name": "Contract", "type": "legal"},
            {"id": "payout", "name": "Payment Notification", "type": "transactional"},
            {"id": "welcome", "name": "Welcome Email", "type": "onboarding"},
            {"id": "notification", "name": "System Notification", "type": "notification"}
        ]

    def _log_dlp_violation(self, sender_id: int, recipient: str, dlp_result: dict, subject: str) -> None:
        try:
            sender_id_val = sender_id if sender_id and self.db.query(User).filter(User.id == sender_id).first() else None
            violation = DLPViolation(
                violation_type="email_dlp",
                severity=dlp_result.get("risk_level", "medium"),
                sender_id=sender_id_val,
                recipient_email=recipient,
                detected_content=subject,
                action_taken="blocked",
                status="pending",
            )
            self.db.add(violation)
            self.db.commit()
        except Exception as exc:
            logger.warning("Failed to log DLP violation: %s", exc)
            self.db.rollback()
    
    def send_bulk_email(self, to_emails: List[str], subject: str, body: str,
                        sender_id: int, template_id: Optional[str] = None) -> dict:
        """Send bulk emails with DLP protection."""
        dlp_result = self.dlp_scanner.scan_content(body)
        
        if not dlp_result["is_safe"]:
            logger.warning(f"Bulk email blocked. Findings: {dlp_result['findings']}")
            self._log_dlp_violation(sender_id, ",".join(to_emails[:5]), dlp_result, subject)
            return {
                "status": "blocked",
                "reason": "DLP violation detected",
                "dlp_findings": dlp_result["findings"],
                "sent_count": 0
            }
        
        sent_count = 0
        failed_count = 0
        failed_emails = []
        
        for email in to_emails:
            try:
                send_email(email, subject, body, purpose="bulk", from_address=get_email_sender_address("bulk"))
                sent_count += 1
            except Exception as e:
                failed_count += 1
                failed_emails.append({"email": email, "error": str(e)})
        
        return {
            "email_id": f"bulk_{datetime.now(timezone.utc).timestamp()}",
            "to_count": len(to_emails),
            "subject": subject,
            "sender_id": sender_id,
            "template_id": template_id,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "sent" if failed_count == 0 else "partial",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "failed_emails": failed_emails[:10]
        }
    
    def get_suppression_list(self) -> List[str]:
        """Get list of suppressed email addresses."""
        return []
    
    def track_open(self, email_id: str, user_id: int) -> dict:
        tracking_url = build_email_open_tracking_url(email_id)
        return {"email_id": email_id, "opened_by": user_id, "opened_at": datetime.now(timezone.utc).isoformat(), "tracking_url": tracking_url}

    def get_email_history(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> dict:
        from data.models import User
        from models.communication import Notification
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"emails": [], "total": 0}

        emails = self.db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()

        return {
            "emails": [
                {
                    "id": e.id,
                    "subject": e.title,
                    "body": e.message,
                    "type": e.type,
                    "is_read": e.is_read,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in emails
            ],
            "total": len(emails),
        }


def get_email_gateway(db: Session) -> EmailGateway:
    return EmailGateway(db)


def _enqueue_email_delivery(email_id: int, body_html: str, subject: str) -> None:
    """Enqueue a background job to deliver an internal email via SMTP."""
    try:
        from utils.background_jobs import enqueue_job, JobKind

        def _deliver() -> dict:
            from data.db import SessionLocal
            from models.communication import InternalEmail
            from utils.email_service import send_email, get_email_sender_address

            db = SessionLocal()
            try:
                email = db.query(InternalEmail).filter(InternalEmail.id == email_id).first()
                if not email:
                    return {"status": "skipped", "reason": "email_not_found"}

                from data.models import User
                recipients = email.recipients or []
                if isinstance(recipients, str):
                    import json
                    recipients = json.loads(recipients)

                for entry in recipients:
                    to_user_id = entry.get("user_id")
                    if not to_user_id:
                        continue
                    user = db.query(User).filter(User.id == to_user_id).first()
                    if user and user.email:
                        from_addr = get_email_sender_address("notification")
                        send_email(
                            to=user.email,
                            subject=subject,
                            html=body_html,
                            purpose="notification",
                            from_address=from_addr,
                        )
                return {"status": "delivered", "email_id": email_id}
            finally:
                db.close()

        enqueue_job(
            kind=JobKind.EMAIL,
            func=_deliver,
            metadata={"email_id": email_id, "subject": subject},
        )
    except Exception as exc:
        logger.debug("Failed to enqueue email delivery: %s", exc)
