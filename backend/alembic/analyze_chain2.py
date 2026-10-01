import re, glob, os
from collections import Counter

versions_dir = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions'
files = sorted(glob.glob(os.path.join(versions_dir, '*.py')))
files = [f for f in files if os.path.basename(f) not in ('__init__.py', 'check_chain.py')]

# Map filename -> revision
file_rev = {}
for f in files:
    with open(f) as fh:
        content = fh.read()
    # Handle all revision declaration styles
    m = re.search(r"revision(?:\s*:\s*str)?\s*=\s*['\"]([^\"'\s]+)", content)
    if m:
        file_rev[f] = m.group(1)
    else:
        file_rev[f] = 'UNKNOWN'

# Check for duplicates
rev_counts = Counter(file_rev.values())
duplicates = {rev: count for rev, count in rev_counts.items() if count > 1}
print('Duplicate revision IDs:')
for rev, count in duplicates.items():
    for f, r in file_rev.items():
        if r == rev:
            print(f'  {os.path.basename(f)} -> {rev}')

# Now build full chain
print()
print('Full chain analysis:')
revision_map = {}
down_revision_map = {}

for f in files:
    with open(f) as fh:
        content = fh.read()
    rev_match = re.search(r"revision[:\s]+['\"]([^\"'\s]+)", content)
    down_match = re.search(r"down_revision[:\s=]+['\"]([^\"'\s]+)", content)
    if rev_match:
        rev = rev_match.group(1)
        revision_map[f] = rev
        if down_match:
            down = down_match.group(1)
            # Handle tuple
            if down.startswith('('):
                down = down.strip('()').replace("'", "").replace('"', '')
                # For tuples, just note them
                down_revision_map[rev] = f"TUPLE({down})"
            else:
                down_revision_map[rev] = down

for f in files:
    rev = revision_map.get(f, '?')
    down = down_revision_map.get(rev, 'None')
    print(f'  {rev} <- {down}')

print()
all_revs = set(revision_map.values())
all_downs = set()
for v in down_revision_map.values():
    if v.startswith('TUPLE('):
        # Extract individual parents
        inner = v[6:-1]
        for parent in inner.split(','):
            all_downs.add(parent.strip())
    elif v != 'None':
        all_downs.add(v)

heads = all_revs - all_downs
print('Heads (divergent):', sorted(heads))

missing = []
for rev, down in down_revision_map.items():
    if down.startswith('TUPLE('):
        inner = down[6:-1]
        for parent in inner.split(','):
            p = parent.strip()
            if p and p not in revision_map.values():
                missing.append((rev, p))
    elif down != 'None' and down not in revision_map.values():
        missing.append((rev, down))
print('Missing down revisions:', missing)
