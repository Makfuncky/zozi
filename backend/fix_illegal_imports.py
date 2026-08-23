"""
Fix illegal cross-domain model imports across the comms domain.
Converts `from domains.{other}.models.` to `from domains.{other}.ports import`.
"""
import os
import re

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'
COMMS = os.path.join(BACKEND, 'domains', 'comms')

# Map of illegal model imports to their ports equivalents
# Format: (illegal_pattern, replacement)
REPLACEMENTS = [
    # Governance models -> governance.ports
    ('from domains.governance.models.user import User', 'from domains.governance.ports import User'),
    ('from domains.governance.models.core import EntityChatThread', 'from domains.governance.ports import EntityChatThread'),
    ('from domains.governance.models.core import EntityChatMessage', 'from domains.governance.ports import EntityChatMessage'),
    ('from domains.governance.models.core import DirectChatRoom', 'from domains.governance.ports import DirectChatRoom'),
    ('from domains.governance.models.core import DirectChatMessage', 'from domains.governance.ports import DirectChatMessage'),
    ('from domains.governance.models.core import GroupChatRoom', 'from domains.governance.ports import GroupChatRoom'),
    ('from domains.governance.models.core import GroupChatMessage', 'from domains.governance.ports import GroupChatMessage'),
    ('from domains.governance.models.core import SupportTicket', 'from domains.governance.ports import SupportTicket'),
    ('from domains.governance.models.core import VideoRoom', 'from domains.governance.ports import VideoRoom'),
    ('from domains.governance.models.admin import TicketReply', 'from domains.governance.ports import TicketReply'),

    # HR models -> hr.ports
    ('from domains.hr.models.employee_models import Employee', 'from domains.hr.ports import Employee'),

    # Finance models -> finance.ports
    ('from domains.finance.models.finance import', 'from domains.finance.ports import'),
    ('from domains.finance.models.erp import', 'from domains.finance.ports import'),

    # Catalog models -> catalog.ports
    ('from domains.catalog.models.products import', 'from domains.catalog.ports import'),

    # Country models -> country.ports
    ('from domains.country.models.countries import', 'from domains.country.ports import'),
    ('from domains.country.models.country_enhancements import', 'from domains.country.ports import'),

    # Media models -> media.ports
    ('from domains.media.models.media_models import', 'from domains.media.ports import'),
    ('from domains.media.models.upload_job import', 'from domains.media.ports import'),

    # Payments models -> payments.ports
    ('from domains.finance.models.payments import', 'from domains.finance.ports import'),

    # Logistics models -> logistics.ports
    ('from domains.logistics.models.logistics import', 'from domains.logistics.ports import'),
]

fixed_files = []

for root, dirs, files in os.walk(COMMS):
    for f in files:
        if f.endswith('.py'):
            filepath = os.path.join(root, f)
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as fh:
                    content = fh.read()

                original = content
                for old, new in REPLACEMENTS:
                    content = content.replace(old, new)

                if content != original:
                    with open(filepath, 'w', encoding='utf-8') as fh:
                        fh.write(content)
                    fixed_files.append(os.path.relpath(filepath, BACKEND))
            except Exception as e:
                pass

print(f"Fixed illegal model imports in {len(fixed_files)} files:")
for f in fixed_files:
    print(f"  - {f}")
