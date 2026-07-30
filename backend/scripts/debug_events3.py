from pathlib import Path

content = Path('models/events.py').read_text()
check = '"schema": "analytics"'
print(f'Contains {check}: {check in content}')
print(f'Contains schema: {"schema" in content}')
