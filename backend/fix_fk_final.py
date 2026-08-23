"""Fix DBA06 violations in marketing.py - change core.users to accounts.users"""
import re

filepath = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\comms\models\marketing.py'
with open(filepath, 'r', encoding='utf-8-sig') as f:
    content = f.read()

# Fix both FK references from core.users to accounts.users
content = content.replace(
    "ForeignKey('core.users.id'",
    "ForeignKey('accounts.users.id'"
)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

# Count replacements
count = content.count("ForeignKey('accounts.users.id'")
print(f'OK: Fixed FK references in marketing.py ({count} references updated)')
