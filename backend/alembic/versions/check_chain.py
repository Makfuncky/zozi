import re
import os
from collections import defaultdict

files = [f for f in os.listdir('.') if f.endswith('.py') and f != '__init__.py']
down_revisions = {}
revisions = {}

for f in files:
    with open(f, 'r') as fh:
        content = fh.read()
    rev_match = re.search(r'revision:\s*str\s*=\s*["\']([^"\']+)["\']', content)
    down_match = re.search(r'down_revision:\s*Union\[str,\s*None\]\s*=\s*["\']([^"\']+)["\']', content)
    if rev_match:
        rev = rev_match.group(1)
        revisions[f] = rev
        if down_match:
            down_revisions[rev] = down_match.group(1)

children = defaultdict(list)
for rev, down in down_revisions.items():
    if down:
        children[down].append(rev)

forks = {k: v for k, v in children.items() if len(v) > 1}
print('Forks:', forks)
print('Total revisions:', len(revisions))
