import re
from pathlib import Path

py = Path('models/events.py')
source = py.read_text()

schema = 'analytics'
table_name = 'outbox_events'

print(f'Looking for tablename: {table_name}')
print(f'Schema: {schema}')

tablename_pattern = re.compile(
    r'(__tablename__\s*=\s*"'
    + re.escape(table_name)
    + r'")',
    re.MULTILINE,
)
match = tablename_pattern.search(source)
print(f'Found tablename match: {match is not None}')

if match:
    start = match.start()
    lines_after = source[match.end():].splitlines(keepends=True)
    insert_point = match.end()
    
    consumed = 0
    found_table_args = False
    for line in lines_after:
        stripped = line.strip()
        if stripped.startswith('__table_args__'):
            found_table_args = True
            break
        if stripped and not stripped.startswith('#') and not stripped.startswith('"""') and not stripped.startswith("'''"):
            break
        consumed += len(line)
        if consumed > 400:
            break
    
    print(f'Found __table_args__: {found_table_args}')
    
    if found_table_args:
        args_pattern = re.compile(
            r'(__table_args__\s*=\s*\()(\s*)(.*?)(\s*)\)',
            re.DOTALL,
        )
        new_source, count = args_pattern.subn(
            lambda m, s=schema: m.group(1)
            + m.group(2)
            + '{"schema": "'
            + s
            + '"}, '
            + m.group(3).lstrip()
            + m.group(4),
            source,
        )
        print(f'Regex replacement count: {count}')
