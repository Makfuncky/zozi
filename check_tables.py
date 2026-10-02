import re
import os
from collections import Counter

tablenames = []
for root, dirs, files in os.walk('backend/domains'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='replace') as fh:
                content = fh.read()
            matches = re.findall(r'__tablename__\s*=\s*["\']([^"\']+)["\']', content)
            for m in matches:
                tablenames.append((m, path))

counter = Counter(t[0] for t in tablenames)
duplicates = {k: v for k, v in counter.items() if v > 1}
if duplicates:
    print('DUPLICATE TABLENAMES:')
    for name, count in duplicates.items():
        paths = [t[1] for t in tablenames if t[0] == name]
        print(f'  {name}: {count} times')
        for p in paths:
            print(f'    - {p}')
else:
    print('NO DUPLICATE TABLENAMES FOUND')
