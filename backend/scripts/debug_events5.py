from pathlib import Path

content = Path('models/events.py').read_text()
check1 = '"schema": "analytics"'
check2 = "'schema': 'analytics'"
print(f'check1 in content: {check1 in content}')
print(f'check2 in content: {check2 in content}')
print(f'Content around __table_args__:')
for i, line in enumerate(content.splitlines()):
    if '__table_args__' in line:
        print(f'  Line {i+1}: {line}')
