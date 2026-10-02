import re
from pathlib import Path

root = Path('src')
input_pattern = re.compile(r'<input\b[^>]*\btype\s*=\s*["\']hidden["\']', re.IGNORECASE)
count = 0
for path in root.rglob('*'):
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    count += len(input_pattern.findall(text))
print('hidden_inputs', count)
