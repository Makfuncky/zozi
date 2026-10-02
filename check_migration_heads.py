import ast
import os
import re

versions_dir = 'backend/alembic/versions'
files = [f for f in os.listdir(versions_dir) if f.endswith('.py') and f != '__init__.py']

revisions = {}
down_revisions = {}

for fname in files:
    path = os.path.join(versions_dir, fname)
    with open(path) as f:
        content = f.read()
    
    # Try annotated format first: revision: str = '...'
    rev_match = re.search(r"revision\s*:\s*str\s*=\s*['\"]([^'\"]+)['\"]", content)
    down_match = re.search(r"down_revision\s*:\s*Union\[str,\s*None\]\s*=\s*(\([^)]*\)|[^#\n]+)", content)
    
    # Fall back to old format: revision = "..."
    if not rev_match:
        rev_match = re.search(r"^revision\s*=\s*['\"]([^'\"]+)['\"]", content, re.MULTILINE)
    if not down_match:
        down_match = re.search(r"^down_revision\s*=\s*(\([^)]*\)|[^#\n]+)", content, re.MULTILINE)
    
    if rev_match:
        rev = rev_match.group(1)
        revisions[rev] = fname
        if down_match:
            down_str = down_match.group(1).strip()
            try:
                down_val = ast.literal_eval(down_str)
                if isinstance(down_val, str):
                    down_revisions[rev] = [down_val]
                elif isinstance(down_val, (list, tuple)):
                    down_revisions[rev] = list(down_val)
                else:
                    down_revisions[rev] = []
            except:
                down_revisions[rev] = []
        else:
            down_revisions[rev] = []

print('Total revisions:', len(revisions))
print()

# Find heads: revisions that are NOT pointed to by any other revision's down_revision
all_children = set()
for downs in down_revisions.values():
    for d in downs:
        if d:
            all_children.add(d)

heads = [rev for rev in revisions if rev not in all_children]
print('Heads (not children of any other):', len(heads))
for h in heads:
    print(f'  {h} ({revisions[h]})')

print()
print('Revisions with multiple down_revisions (merge migrations):')
for rev, downs in down_revisions.items():
    if len(downs) > 1:
        print(f'  {rev}: {downs}')

print()
print('Orphans (down_revision points to non-existent revision):')
for rev, downs in down_revisions.items():
    for d in downs:
        if d and d not in revisions:
            print(f'  {rev} -> {d} (MISSING)')
