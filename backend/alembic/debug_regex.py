import re, glob, os
from collections import Counter

versions_dir = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions'
files = sorted(glob.glob(os.path.join(versions_dir, '*.py')))
files = [f for f in files if os.path.basename(f) not in ('__init__.py', 'check_chain.py')]

print(f'Total files: {len(files)}')
print()

# Map filename -> revision
file_rev = {}
for f in files[:5]:
    with open(f) as fh:
        content = fh.read()
    print(f'File: {os.path.basename(f)}')
    print(f'  First 200 chars: {repr(content[:200])}')
    # Try various patterns
    for pattern in [
        r"revision:\s*str\s*=\s*['\"]([^\"'\s]+)",
        r"revision\s*=\s*['\"]([^\"'\s]+)",
        r"revision[:\s]+['\"]([^\"'\s]+)",
    ]:
        m = re.search(pattern, content)
        if m:
            print(f'  Pattern {pattern[:30]}... matched: {m.group(1)}')
    print()
