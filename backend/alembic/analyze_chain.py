import os, re, glob

versions_dir = 'versions'
files = sorted(glob.glob(os.path.join(versions_dir, '*.py')))
files = [f for f in files if os.path.basename(f) not in ('__init__.py', 'check_chain.py')]

print('Total migration files:', len(files))
print()

# Build revision map
revision_map = {}
down_revision_map = {}

for f in files:
    with open(f) as fh:
        content = fh.read()
    rev_match = re.search(r'revision:\s*(?:str\s*=\s*)?["\']+([^"\'\s]+)', content)
    down_match = re.search(r'down_revision:\s*(?:Union\[str,\s*None\]\s*=\s*)?["\']+([^"\'\s]+)', content)
    if rev_match:
        rev = rev_match.group(1)
        revision_map[f] = rev
        if down_match:
            down = down_match.group(1)
            down_revision_map[rev] = down

print('Revision chain:')
for f in files:
    rev = revision_map.get(f, '?')
    down = down_revision_map.get(rev, 'None')
    print(f'  {rev} <- {down}')

print()
# Find heads
all_revs = set(revision_map.values())
all_downs = set(v for v in down_revision_map.values() if v and v != 'None')
heads = all_revs - all_downs
print('Heads (divergent):', heads)

# Find missing down revisions
missing = []
for rev, down in down_revision_map.items():
    if down and down not in revision_map.values():
        missing.append((rev, down))
print('Missing down revisions:', missing)

# Check for tuples (merge migrations)
tuples = {rev: down for rev, down in down_revision_map.items() if down and down.startswith('(')}
print('Tuple down_revisions (merges):', tuples)
