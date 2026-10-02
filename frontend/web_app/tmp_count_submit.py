import re
from pathlib import Path

root = Path('src')
button_tag = re.compile(r'<button\b')
type_submit = re.compile(r'type\s*=\s*["\']submit["\']')
count_submit = 0
for path in root.rglob('*'):
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    for m in button_tag.finditer(text):
        start = m.start()
        end = text.find('>', start)
        if end == -1:
            end = start + 200
        tag = text[start:end]
        if type_submit.search(tag):
            count_submit += 1
print('buttons_with_type_submit', count_submit)
