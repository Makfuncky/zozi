"""
Fix duplicate table definitions in governance/models/core.py, finance/models/general_ledger.py, and governance/models/admin.py.
Convert duplicates to re-export shims from canonical domains.
"""
import os

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'

# Fix governance/models/core.py
gov_core_path = os.path.join(BACKEND, 'domains', 'governance', 'models', 'core.py')
with open(gov_core_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace AuditLog class with re-export
old_audit_log = '''class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = ({"schema": "audit"},)
    id = Column(Integer, primary_key=True, index=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=True)
    username = Column(String, nullable=True)
    user_role = Column(String, nullable=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)


class SupportTicket'''

new_audit_log = '''# Re-export from canonical audit domain (was duplicate definition)
from domains.audit.models.audit_schema_models import AuditLog  # noqa: F401


class SupportTicket'''

if old_audit_log in content:
    content = content.replace(old_audit_log, new_audit_log)
    print('OK: Replaced AuditLog duplicate in governance/core.py')
else:
    print('WARN: AuditLog pattern not found in governance/core.py')

# Replace SupportTicket, SupportTicketReply, TicketAttachment with re-exports from comms
old_support = '''class SupportTicket(Base):
    __tablename__ = "support_tickets"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    subject = Column(String, nullable=False)
    priority = Column(String, default="medium")
    status = Column(String, default="open")
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    replies = relationship("SupportTicketReply", back_populates="ticket")
    attachments = relationship("TicketAttachment", back_populates="ticket")
    messages = relationship("TicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketReply(Base):
    __tablename__ = "support_ticket_replies"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("core.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    ticket = relationship("SupportTicket", back_populates="replies")
    attachments = relationship("TicketAttachment", back_populates="ticket_reply")


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"
    __table_args__ = ({"schema": "communication"},)
    id = Column(Integer, primary_key=True, index=True)
    ticket_reply_id = Column(Integer, ForeignKey("support_ticket_replies.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("communication.support_tickets.id"), nullable=True)
    file_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    country_code = Column(String(10), nullable=True, index=True)
    ticket_reply = relationship("SupportTicketReply", back_populates="attachments")
    ticket = relationship("SupportTicket", back_populates="attachments")'''

new_support = '''# Re-export from canonical comms domain (were duplicate definitions)
from domains.comms.models.communication_schema_models import (  # noqa: F401
    SupportTicket, SupportTicketReply, TicketAttachment,
)'''

if old_support in content:
    content = content.replace(old_support, new_support)
    print('OK: Replaced SupportTicket duplicates in governance/core.py')
else:
    print('WARN: SupportTicket pattern not found in governance/core.py')

with open(gov_core_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Done fixing governance/core.py')
