import re
from pathlib import Path

root = Path('src')
input_pattern = re.compile(r'<input\b[^>]*\btype\s*=\s*["\']([^"\']+)["\']')
type_counts = {}
for path in root.rglob('*'):
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    for m in input_pattern.finditer(text):
        t = m.group(1).lower()
        type_counts[t] = type_counts.get(t, 0) + 1
for k, v in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f'{k}: {v}')
