import ast
from pathlib import Path

py = Path('models/events.py')
source = py.read_text()
tree = ast.parse(source)

SCHEMA_MAPPING = {
    'outbox_events': 'analytics',
    'inbox_events': 'analytics',
    'event_retry_queue': 'analytics',
    'event_dead_letter': 'analytics',
}

for node in tree.body:
    if isinstance(node, ast.ClassDef):
        tablename = None
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == '__tablename__':
                        tablename = item.value.value
        if tablename:
            schema = SCHEMA_MAPPING.get(tablename)
            print(f'{tablename} -> {schema}')
            if schema and schema != 'public':
                schema_present = "schema" in source
                print(f'  schema_present={schema_present}')
