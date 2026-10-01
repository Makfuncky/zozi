import re, glob, os

versions_dir = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions'
files = sorted(glob.glob(os.path.join(versions_dir, '*.py')))
files = [f for f in files if os.path.basename(f) not in ('__init__.py', 'check_chain.py')]

print(f'Total files: {len(files)}')
print()

# Map filename -> revision and down_revision
revision_map = {}  # revision_id -> filename
down_rev_map = {}  # revision_id -> down_revision

for f in files:
    fname = os.path.basename(f)
    with open(f) as fh:
        content = fh.read()
    
    # Find revision ID
    m = re.search(r"revision:\s*str\s*=\s*['\"]([^\"'\s]+)", content)
    if not m:
        m = re.search(r"revision\s*=\s*['\"]([^\"'\s]+)", content)
    if m:
        rev_id = m.group(1)
        revision_map[rev_id] = fname
    else:
        print(f'  WARNING: No revision found in {fname}')
        continue
    
    # Find down_revision
    m2 = re.search(r"down_revision:\s*Union\[str,\s*None\]\s*=\s*['\"]([^\"'\s]+)", content)
    if not m2:
        m2 = re.search(r"down_revision\s*=\s*['\"]([^\"'\s]+)", content)
    if m2:
        down = m2.group(1)
        down_rev_map[rev_id] = down
    else:
        # Check for tuple
        m3 = re.search(r"down_revision:\s*Union\[Tuple\[str,\s*str\],\s*None\]\s*=\s*\(([^)]+)\)", content)
        if m3:
            down_rev_map[rev_id] = f"TUPLE({m3.group(1)})"
        else:
            down_rev_map[rev_id] = None

# Check for duplicate revision IDs
rev_to_files = {}
for f in files:
    fname = os.path.basename(f)
    with open(f) as fh:
        content = fh.read()
    m = re.search(r"revision:\s*str\s*=\s*['\"]([^\"'\s]+)", content)
    if not m:
        m = re.search(r"revision\s*=\s*['\"]([^\"'\s]+)", content)
    if m:
        rev = m.group(1)
        rev_to_files.setdefault(rev, []).append(fname)

duplicates = {rev: files_list for rev, files_list in rev_to_files.items() if len(files_list) > 1}
print('DUPLICATE REVISION IDs:')
for rev, flist in duplicates.items():
    print(f'  Revision {rev}: {flist}')
print()

# Build chain
print('MIGRATION CHAIN:')
for f in files:
    fname = os.path.basename(f)
    with open(f) as fh:
        content = fh.read()
    m = re.search(r"revision:\s*str\s*=\s*['\"]([^\"'\s]+)", content)
    if not m:
        m = re.search(r"revision\s*=\s*['\"]([^\"'\s]+)", content)
    if not m:
        continue
    rev = m.group(1)
    down = down_rev_map.get(rev, '?')
    print(f'  {rev}  <-  {down}')

print()

# Find heads
all_revs = set(revision_map.keys())
all_down_revs = set()
for v in down_rev_map.values():
    if v and v.startswith('TUPLE('):
        inner = v[6:-1]
        for p in inner.split(','):
            all_down_revs.add(p.strip().strip("'\""))
    elif v:
        all_down_revs.add(v)

heads = all_revs - all_down_revs
print(f'HEADS (divergent): {sorted(heads)}')
print()

# Missing down revisions
missing = []
for rev, down in down_rev_map.items():
    if down and not down.startswith('TUPLE('):
        if down not in revision_map:
            missing.append((rev, down))
    elif down and down.startswith('TUPLE('):
        inner = down[6:-1]
        for p in inner.split(','):
            p = p.strip().strip("'\"")
            if p and p not in revision_map:
                missing.append((rev, p))
print(f'MISSING DOWN REVISIONS: {missing}')
print()

# Naming convention check
print('NAMING CONVENTION CHECK:')
import re
TIMESTAMP_RE = re.compile(r'^(\d{4})_(\d{2})_(\d{2})_(\d{2})_(\d{2})')
for f in files:
    fname = os.path.basename(f)
    stem = fname[:-3]
    ts_match = TIMESTAMP_RE.match(stem)
    if ts_match:
        expected = f"{ts_match.group(1)}{ts_match.group(2)}{ts_match.group(3)}_{ts_match.group(4)}{ts_match.group(5)}"
        with open(f) as fh:
            content = fh.read()
        m = re.search(r"revision:\s*str\s*=\s*['\"]([^\"'\s]+)", content)
        if not m:
            m = re.search(r"revision\s*=\s*['\"]([^\"'\s]+)", content)
        if m:
            file_rev = m.group(1)
            if not file_rev.startswith(expected):
                print(f'  MISMATCH: {fname} (expected prefix {expected}, got {file_rev})')
    else:
        print(f'  NO TIMESTAMP PREFIX: {fname}')
