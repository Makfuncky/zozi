import os
from pathlib import Path

p = Path('backend/main.py')
print(f'exists: {p.exists()}')
if p.exists():
    print(f'stat: {os.stat(p)}')

# Check what rglob found
for f in Path('.').rglob('main.py'):
    s = str(f)
    if 'venv' not in s and 'site-packages' not in s and '.kilo' not in s and 'node_modules' not in s:
        print(f'Found: {f} -> exists={f.exists()}')
        if f.exists():
            print(f'  stat: {os.stat(f)}')
