#!/usr/bin/env python3
import os
import sys
import glob

os.chdir(os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.join('..', 'backend'))

files = glob.glob('**/*.py', recursive=True)
skip = {'__pycache__', 'venv', '.git', '_extra_files', 'tests', 'scripts'}

fixed = []
for fpath in files:
    parts = fpath.replace('\\', '/').split('/')
    if any(p in skip for p in parts):
        continue
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        continue

    if 'logger.exception(' not in content:
        continue
    if 'logger = ' in content or 'logger= ' in content:
        continue

    lines = content.split('\n')
    insert_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith('import ') or stripped.startswith('from '):
            insert_idx = i + 1

    has_logging = 'import logging' in content
    if has_logging:
        logger_line = 'logger = logging.getLogger(__name__)'
    else:
        logger_line = 'import logging\nlogger = logging.getLogger(__name__)'

    lines.insert(insert_idx, logger_line)
    lines.insert(insert_idx + 1, '')

    with open(fpath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    fixed.append(fpath)

print(f'Added logger to {len(fixed)} files')
for f in fixed:
    print(f'  {f}')
