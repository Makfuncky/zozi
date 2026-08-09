import re
from pathlib import Path

py = Path('models/events.py')
source = py.read_text()
table_name = 'outbox_events'
schema = 'analytics'

print(f'Processing: {table_name} -> {schema}')

if '"schema": "analytics"' in source or "'schema': 'analytics'" in source:
    print('SKIP: schema already present')
else:
    print('Schema not present, proceeding...')
    
    tablename_pattern = re.compile(
        r'(__tablename__\s*=\s*"'
        + re.escape(table_name)
        + r'")',
        re.MULTILINE,
    )
    match = tablename_pattern.search(source)
    print(f'Found tablename: {match is not None}')
    
    if match:
        start = match.start()
        lines_after = source[match.end():].splitlines(keepends=True)
        insert_point = match.end()
        
        consumed = 0
        found_table_args = False
        for i, line in enumerate(lines_after):
            stripped = line.strip()
            print(f'  Line {i}: {repr(stripped[:60])}')
            if stripped.startswith("__table_args__"):
                found_table_args = True
                break
            if stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
                break
            consumed += len(line)
            if consumed > 400:
                break
        
        print(f'Found __table_args__: {found_table_args}')
