"""
Fix all broken import paths in comms services.
"""
import os
import re

BACKEND = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend'

# All broken import fixes
fixes = [
    # Broken intra-domain imports
    {
        'file': os.path.join(BACKEND, 'domains', 'comms', 'services', 'shared', 'admin', 'communication_audit_controller.py'),
        'old': 'from domains.comms.services.admin.communication_audit import',
        'new': 'from domains.comms.services.shared.admin.communication_audit import',
    },
    {
        'file': os.path.join(BACKEND, 'domains', 'comms', 'services', 'shared', 'notification', 'notification_controller.py'),
        'old': 'from domains.comms.services.notification.notification_engine import',
        'new': 'from domains.comms.services.shared.notification.notification_engine import',
    },
    {
        'file': os.path.join(BACKEND, 'domains', 'comms', 'services', 'marketing', 'transactional_email.py'),
        'old': 'from domains.comms.services.email_event_service import',
        'new': 'from domains.comms.services.marketing.email_event_service import',
    },
    {
        'file': os.path.join(BACKEND, 'domains', 'comms', 'services', 'channel', 'internal_comms_channels_service.py'),
        'old': 'from domains.comms.services.channel.internal_communication import',
        'new': 'from domains.comms.services.messaging.channel.internal_communication import',
    },
    {
        'file': os.path.join(BACKEND, 'domains', 'comms', 'services', 'internal_channels_service.py'),
        'old': 'from domains.comms.services.channel.internal_communication import',
        'new': 'from domains.comms.services.messaging.channel.internal_communication import',
    },
]

for fix in fixes:
    filepath = fix['file']
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        if fix['old'] in content:
            content = content.replace(fix['old'], fix['new'])
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'Fixed: {os.path.relpath(filepath, BACKEND)}')
        else:
            print(f'Pattern not found: {os.path.relpath(filepath, BACKEND)}')
    else:
        print(f'File not found: {os.path.relpath(filepath, BACKEND)}')

print('\nDone fixing broken import paths.')
