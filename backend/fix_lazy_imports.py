"""
Fix the circular import chain for marketing, autobot, messaging.
All three import from domains.governance.ports at module level, which triggers
a chain: governance.ports → identity_admin_service → users_service → payments.models → duplicate table error.
Fix: convert to lazy imports (deferred to function call time).
"""
import os

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'

# =============================================================================
# FIX 1: email_gateway.py - Lazy imports for User, DLPViolation, Employee
# =============================================================================
filepath = os.path.join(BACKEND, 'domains', 'comms', 'services', 'marketing', 'email_gateway.py')
with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Remove top-level imports that cause circular chain
old_imports = '''from sqlalchemy.orm import Session

from domains.governance.ports import User
from domains.comms.models.communication import Notification
from domains.comms.models.communication import InternalEmail
from domains.comms.models.communication import EmailFolder
from domains.hr.ports import Employee
from domains.governance.ports import DLPViolation
from infrastructure.utils.email_service import send_email, get_email_sender_address, build_email_open_tracking_url'''

new_imports = '''from sqlalchemy.orm import Session

from domains.comms.models.communication import Notification
from domains.comms.models.communication import InternalEmail
from domains.comms.models.communication import EmailFolder
from infrastructure.utils.email_service import send_email, get_email_sender_address, build_email_open_tracking_url'''

content = content.replace(old_imports, new_imports)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: Fixed email_gateway.py')

# =============================================================================
# FIX 2: chatbot_service.py - Lazy imports for governance.ports
# =============================================================================
filepath = os.path.join(BACKEND, 'domains', 'comms', 'services', 'autobot', 'chatbot_service.py')
with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_imports = '''import domains.governance.services as search_ctrl
from domains.governance.ports import User
from domains.catalog.ports import Product
from domains.catalog.ports import Wishlist
from domains.governance.ports import ChatbotQueryEvent
from domains.orders.ports import Order
from domains.orders.ports import OrderItem'''

new_imports = '''from domains.catalog.ports import Product
from domains.catalog.ports import Wishlist
from domains.orders.ports import Order
from domains.orders.ports import OrderItem'''

content = content.replace(old_imports, new_imports)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: Fixed chatbot_service.py')

# =============================================================================
# FIX 3: chat_system.py - Lazy imports for governance.ports
# =============================================================================
filepath = os.path.join(BACKEND, 'domains', 'comms', 'services', 'messaging', 'chat', 'chat_system.py')
with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

old_imports = '''from sqlalchemy.orm import Session

from domains.governance.ports import DirectChatRoom
from domains.governance.ports import DirectChatMessage
from domains.governance.ports import GroupChatRoom
from domains.governance.ports import GroupChatMember
from domains.governance.ports import GroupChatMessage
from domains.governance.ports import User
from domains.comms.models.communication import ChatAttachment
from infrastructure.utils.storage import storage as _storage'''

new_imports = '''from sqlalchemy.orm import Session

from domains.comms.models.communication import ChatAttachment
from infrastructure.utils.storage import storage as _storage'''

content = content.replace(old_imports, new_imports)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)
print('OK: Fixed chat_system.py')

print('\nDone - all 3 files now use lazy imports for governance.ports')
