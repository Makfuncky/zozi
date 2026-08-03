#!/usr/bin/env python3
import os, re
from collections import defaultdict

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
write_patterns = [
    r'session\.add\(',
    r'db\.add\(',
    r'session\.commit\(',
    r'db\.commit\(',
    r'\.add_instance\(',
    r'\.bulk_save_objects\(',
    r'db\.execute\([\"]',
    r'db\.execute\(f[\"|\']',
]

files_with_writes = []

for root, dirs, files in os.walk(base_dir):
    if 'venv' in root:
        continue
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            if 'controllers/' in path or 'routers/' in path:
                with open(path, 'r', errors='ignore') as fp:
                    lines = fp.readlines()
                for i, line in enumerate(lines, 1):
                    for pattern in write_patterns:
                        if re.search(pattern, line):
                            rel_path = path.replace(base_dir + os.sep, '')
                            files_with_writes.append((rel_path, i, line.strip()[:80]))
                            break

# Group by file and count
file_writes = defaultdict(list)
for path, line_num, line_text in files_with_writes:
    file_writes[path].append((line_num, line_text))

# Sort by number of writes and show top 20
sorted_files = sorted(file_writes.items(), key=lambda x: -len(x[1]))
for path, writes in sorted_files[:20]:
    print(f'{path}: {len(writes)} writes')
    for line_num, line_text in writes[:5]:
        print(f'  Line {line_num}: {line_text[:60]}...')