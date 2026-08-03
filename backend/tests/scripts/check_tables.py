#!/usr/bin/env python
"""Check table names in models."""
import os
import re

actual_tables = {}

for root, dirs, files in os.walk('backend/models'):
    for f in files:
        if f.endswith('.py') and f != '__init__.py':
            filepath = os.path.join(root, f)
            with open(filepath, 'r') as file:
                content = file.read()
                if 'country_code' in content:
                    tablename_matches = re.findall(r'__tablename__\s*=\s*["\']([^"\']+)["\']', content)
                    for table in tablename_matches:
                        actual_tables[table] = True

print('Actual table names with country_code:')
for t in sorted(actual_tables):
    print(f'  {t}')