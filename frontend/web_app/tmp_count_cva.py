import re
from pathlib import Path

root = Path('src')
# Check for cva usage across entire src
cva_pattern = re.compile(r'\bcva\(')
count = 0
files = set()
for path in root.rglob('*'):
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    if cva_pattern.search(text):
        count += 1
        files.add(str(path))
print('files_with_cva', count)
for f in sorted(files):
    print(' ', f)
