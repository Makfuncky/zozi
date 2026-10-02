from pathlib import Path
import re

content = Path('frontend/web_app/package.json').read_text(encoding='utf-8', errors='ignore')
ts = re.search(r'"typescript"\s*:\s*"[^"]*"', content)
print('typescript line:', ts.group(0) if ts else 'NONE')
print('--- lines around typescript ---')
for i, line in enumerate(content.split('\n'), 1):
    if 'typescript' in line.lower():
        print(f'{i}: {line}')
