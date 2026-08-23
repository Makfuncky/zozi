"""
Fix schema violations in comms models:
1. Normalize chat.py schemas to 'comms'
2. Fix FK references to use correct schema prefixes
3. Remove duplicate table definitions from communication_schema_models.py
4. Fix FK schema mismatches in communication.py and marketing.py
"""
import os
import re

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'

# =============================================================================
# FIX 1: chat.py - Normalize schemas to comms
# =============================================================================
chat_path = os.path.join(BACKEND, 'domains', 'comms', 'models', 'chat.py')

with open(chat_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace all schema declarations with comms
content = content.replace('{"schema": "customer"}', '{"schema": "comms"}')
content = content.replace('{"schema": "communication"}', '{"schema": "comms"}')
content = content.replace('{"schema": "media"}', '{"schema": "comms"}')

# Fix FK references - replace customer. and communication. prefixes with comms.
content = content.replace('ForeignKey("customer.video_rooms.id")', 'ForeignKey("comms.video_rooms.id")')
content = content.replace('ForeignKey("customer.direct_chat_rooms.id")', 'ForeignKey("comms.direct_chat_rooms.id")')
content = content.replace('ForeignKey("entity_chat_threads.id")', 'ForeignKey("comms.entity_chat_threads.id")')

# Fix idx_entity_thread to ix_entity_thread (naming convention)
content = content.replace('Index("idx_entity_thread"', 'Index("ix_entity_thread"')

with open(chat_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Fixed chat.py schemas and FK references')

# =============================================================================
# FIX 2: communication_schema_models.py - Remove duplicate table definitions
# =============================================================================
schema_models_path = os.path.join(BACKEND, 'domains', 'comms', 'models', 'communication_schema_models.py')

with open(schema_models_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Replace duplicate class definitions with re-exports from chat.py
# The duplicate tables are: EntityChatMessage, DirectChatMessage, GroupChatRoom, GroupChatMessage

# Find and replace the duplicate EntityChatMessage class
old_entity_msg = '''class EntityChatMessage(Base):
    __tablename__ = "entity_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey("customer.entity_chat_threads.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    thread = relationship("EntityChatThread", back_populates="messages")
    sender = relationship("User")'''

new_entity_msg = '''# Re-export from canonical chat.py (was duplicate definition)
from domains.comms.models.chat import EntityChatMessage  # noqa: F401'''

if old_entity_msg in content:
    content = content.replace(old_entity_msg, new_entity_msg)
    print('  - Replaced EntityChatMessage duplicate')
else:
    print('  - EntityChatMessage: already fixed or pattern not found')

# Find and replace the duplicate DirectChatMessage class
old_direct_msg = '''class DirectChatMessage(Base):
    __tablename__ = "direct_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("customer.direct_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    room = relationship("DirectChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])'''

new_direct_msg = '''from domains.comms.models.chat import DirectChatMessage  # noqa: F401'''

if old_direct_msg in content:
    content = content.replace(old_direct_msg, new_direct_msg)
    print('  - Replaced DirectChatMessage duplicate')
else:
    print('  - DirectChatMessage: already fixed or pattern not found')

# Find and replace the duplicate GroupChatRoom class
old_group_room = '''class GroupChatRoom(Base):
    __tablename__ = "group_chat_rooms"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(String(64), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    country_code = Column(String(10), ForeignKey("country.country_configs.code"), nullable=True)
    is_encrypted = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    members = relationship("GroupChatMember", back_populates="room", cascade="all, delete-orphan")
    messages = relationship("GroupChatMessage", back_populates="room", cascade="all, delete-orphan")'''

new_group_room = '''from domains.comms.models.chat import GroupChatRoom  # noqa: F401'''

if old_group_room in content:
    content = content.replace(old_group_room, new_group_room)
    print('  - Replaced GroupChatRoom duplicate')
else:
    print('  - GroupChatRoom: already fixed or pattern not found')

# Find and replace the duplicate GroupChatMessage class
old_group_msg = '''class GroupChatMessage(Base):
    __tablename__ = "group_chat_messages"
    __table_args__ = ({"schema": "comms"},)
    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("comms.group_chat_rooms.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("accounts.users.id"), nullable=False)
    message = Column(Text, nullable=False)
    message_type = Column(String(20), default="text")
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    room = relationship("GroupChatRoom", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])'''

new_group_msg = '''from domains.comms.models.chat import GroupChatMessage  # noqa: F401'''

if old_group_msg in content:
    content = content.replace(old_group_msg, new_group_msg)
    print('  - Replaced GroupChatMessage duplicate')
else:
    print('  - GroupChatMessage: already fixed or pattern not found')

# Fix remaining FK references in communication_schema_models.py
content = content.replace('ForeignKey("customer.entity_chat_threads.id")', 'ForeignKey("comms.entity_chat_threads.id")')
content = content.replace('ForeignKey("customer.direct_chat_rooms.id")', 'ForeignKey("comms.direct_chat_rooms.id")')

# Update __all__ to include re-exports
if 'EntityChatMessage' not in content.split('__all__')[1] if '__all__' in content else True:
    # Already imported via re-export
    pass

with open(schema_models_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Fixed communication_schema_models.py')

# =============================================================================
# FIX 3: communication.py - Fix FK schema mismatches
# =============================================================================
comm_path = os.path.join(BACKEND, 'domains', 'comms', 'models', 'communication.py')

with open(comm_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix FK references from communication. to commms.
content = content.replace('ForeignKey("communication.support_tickets.id"', 'ForeignKey("comms.support_tickets.id"')
content = content.replace('ForeignKey("communication.proxy_channels.id"', 'ForeignKey("comms.proxy_channels.id"')
content = content.replace('ForeignKey("communication.proxy_sessions.id"', 'ForeignKey("comms.proxy_sessions.id"')
content = content.replace('ForeignKey("communication.internal_channels.id"', 'ForeignKey("comms.internal_channels.id"')
content = content.replace('ForeignKey("communication.internal_emails.id"', 'ForeignKey("comms.internal_emails.id"')
content = content.replace('ForeignKey("communication.email_folders.id"', 'ForeignKey("comms.email_folders.id"')

# Remove orphaned Index() objects at module level (dead code)
# These are duplicates of indexes already defined in model __table_args__
lines = content.split('\n')
new_lines = []
skip_orphaned = False
for i, line in enumerate(lines):
    # Check for orphaned Index declarations
    if line.strip().startswith("Index('ix_notifications_variables'") or \
       line.strip().startswith("Index('ix_proxy_channels_participants'") or \
       line.strip().startswith("Index('ix_proxy_sessions_session_metadata'") or \
       line.strip().startswith("Index('ix_communication_audit_trail_metadata_json'") or \
       line.strip().startswith("Index('ix_internal_channels_allowed_roles'"):
        skip_orphaned = True
        continue
    if skip_orphaned:
        # Check if this line ends the Index declaration
        if '),' in line or ')' in line:
            skip_orphaned = False
        continue
    new_lines.append(line)

content = '\n'.join(new_lines)

with open(comm_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Fixed communication.py FK schema mismatches and removed orphaned indexes')

# =============================================================================
# FIX 4: marketing.py - Fix FK schema mismatches
# =============================================================================
marketing_path = os.path.join(BACKEND, 'domains', 'comms', 'models', 'marketing.py')

with open(marketing_path, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix FK references
content = content.replace('ForeignKey("commerce.flash_sales.id"', 'ForeignKey("comms.flash_sales.id"')
content = content.replace('ForeignKey("communication.email_campaigns.id"', 'ForeignKey("comms.email_campaigns.id"')

# Remove orphaned Index() objects at module level
lines = content.split('\n')
new_lines = []
for line in lines:
    if line.strip().startswith("Index('ix_flash_sales_product_ids'") or \
       line.strip().startswith("Index('ix_email_delivery_events_details'"):
        continue
    new_lines.append(line)

content = '\n'.join(new_lines)

with open(marketing_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('OK: Fixed marketing.py FK schema mismatches and removed orphaned indexes')

print('\nDone with schema fixes!')
