"""Add schema declarations to all model files based on schema_mapping.json."""
import json
import re
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
models_dir = backend_dir / "models"
docs_dir = backend_dir / "docs"

with open(docs_dir / "schema_mapping.json") as f:
    table_to_schema = json.load(f)

# Tables that don't have a schema mapping yet - default to public
DEFAULT_SCHEMA = "public"

def get_schema_for_table(table_name: str) -> str:
    return table_to_schema.get(table_name, DEFAULT_SCHEMA)

def update_model_file(file_path: Path):
    content = file_path.read_text()
    original = content

    # Find all class definitions that have __tablename__
    # Pattern: class X(Base):\n    __tablename__ = "table_name"
    class_pattern = re.compile(
        r'(class\s+\w+\(Base\):\s*\n\s*__tablename__\s*=\s*"([^"]+)")',
        re.MULTILINE
    )

    replacements = 0
    for match in class_pattern.finditer(content):
        full_match = match.group(1)
        table_name = match.group(2)
        schema = get_schema_for_table(table_name)

        # Find the __table_args__ that follows this class definition
        # Look for __table_args__ within the next 500 chars after the class start
        class_start = match.start()
        class_end = match.end()
        following = content[class_end:class_end + 800]

        # Check if __table_args__ exists
        table_args_match = re.search(r'(\n\s*__table_args__\s*=\s*)', following)
        if table_args_match:
            # Existing __table_args__ - need to add/replace schema
            # Find the actual __table_args__ value
            args_start = class_end + table_args_match.start(1)
            args_value_start = class_end + table_args_match.end(1)
            
            # Find the end of the __table_args__ value
            # It could be a dict, tuple, or list
            if following.strip().startswith('{'):
                # Dict-style: {"schema": "..."}
                # Check if it already has schema
                if '"schema"' in following[:200] or "'schema'" in following[:200]:
                    continue  # Already has schema
                # Replace with new dict including schema
                old_args = re.search(r'__table_args__\s*=\s*\{[^}]+\}', following)
                if old_args:
                    new_args = f'__table_args__ = {{"schema": "{schema}"}}'
                    content = content[:args_start] + new_args + content[args_start + len(old_args.group(0)):]
                    replacements += 1
            else:
                # Tuple/list style
                # Check if schema dict is already present
                if re.search(r'\{["\']schema["\']:', following[:300]):
                    continue  # Already has schema
                
                # Find the closing parenthesis/bracket
                # We need to be careful here - find the balanced end
                args_str = following[table_args_match.end(1) - args_value_start + args_start - class_end:]
                # Actually, let's just insert schema dict after the opening ( or [
                open_paren = following.find('(', table_args_match.end(1) - args_value_start + args_start - class_end)
                open_bracket = following.find('[', table_args_match.end(1) - args_value_start + args_start - class_end)
                
                # Use regex to find and replace
                old_args_pattern = re.compile(r'__table_args__\s*=\s*(\([^)]+\)|\[[^\]]+\]|\{[^}]+\})')
                old_args_match = old_args_pattern.search(content[args_start:])
                if old_args_match:
                    old_args_str = old_args_match.group(1)
                    if old_args_str.startswith('('):
                        new_args_str = f'({{\"schema\": \"{schema}\"}},{old_args_str[1:]}'
                    elif old_args_str.startswith('['):
                        new_args_str = f'[{{\"schema\": \"{schema}\"}},{old_args_str[1:]}'
                    else:
                        continue
                    content = content[:args_start] + '__table_args__ = ' + new_args_str + content[args_start + len(old_args_str) + 16:]
                    replacements += 1
        else:
            # No __table_args__ exists - add one after __tablename__
            # Insert after the __tablename__ line
            tablename_end = class_end
            insert_point = content.find('\n', tablename_end) + 1
            new_table_args = f'    __table_args__ = {{"schema": "{schema}"}}\n'
            content = content[:insert_point] + new_table_args + content[insert_point:]
            replacements += 1

    if content != original:
        file_path.write_text(content)
        print(f"Updated {file_path.name}: {replacements} classes")
    else:
        print(f"No changes: {file_path.name}")

for model_file in sorted(models_dir.glob('*.py')):
    if model_file.name in ('__init__.py', 'mixins.py'):
        continue
    update_model_file(model_file)
