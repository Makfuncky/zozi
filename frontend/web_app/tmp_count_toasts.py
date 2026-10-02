import re
from pathlib import Path

root = Path('src')
addToast = re.compile(r'addToast\s*\([^,]+,\s*["\'](success|error|info|warning)["\']')
count_success = 0
count_error = 0
count_info = 0
count_warning = 0
for path in root.rglob('*'):
    if not path.is_file():
        continue
    text = path.read_text(encoding='utf-8', errors='ignore')
    for m in addToast.finditer(text):
        t = m.group(1)
        if t == 'success':
            count_success += 1
        elif t == 'error':
            count_error += 1
        elif t == 'info':
            count_info += 1
        elif t == 'warning':
            count_warning += 1
print('addToast_success', count_success)
print('addToast_error', count_error)
print('addToast_info', count_info)
print('addToast_warning', count_warning)
