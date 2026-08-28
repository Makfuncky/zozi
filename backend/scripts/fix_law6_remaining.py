"""Fix remaining Law 6 schema discipline violations."""
from __future__ import annotations

import re
import pathlib

BACKEND_ROOT = pathlib.Path(__file__).resolve().parent.parent
DOMAINS_DIR = BACKEND_ROOT / "domains"

def get_domain(file_path):
    """Extract domain from file path relative to domains dir."""
    try:
        parts = file_path.relative_to(DOMAINS_DIR).parts
        return parts[0] if parts else None
    except ValueError:
        return None

def fix_schema_in_file(source, domain):
    """Add schema declaration within 500 chars of __tablename__ if missing."""
    lines = source.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]
        result.append(line)

        if re.search(r'__tablename__\s*=', line) and '=' in line:
            # Look ahead ~500 chars (about 7 lines) for schema declaration
            lookahead = '\n'.join(lines[i:i+8])
            has_schema = re.search(r"""['"]schema['"]:\s*['"]""", lookahead)

            if not has_schema:
                indent = len(line) - len(line.lstrip())
                indent_str = ' ' * indent
                result.append(f'{indent_str}__table_args__ = {{"schema": "{domain}"}}')

        i += 1

    return '\n'.join(result)


def fix_fk_columns(source):
    """Rename FK columns to use _id suffix.

    Only renames columns that have ForeignKey in their definition.
    """
    # Find all FK columns that don't end in _id
    fk_pattern = re.compile(r'(\w+)\s*=\s*Column\([^)]*ForeignKey')
    matches = list(fk_pattern.finditer(source))

    # Build rename map: old_name -> new_name
    rename_map = {}
    for m in matches:
        col_name = m.group(1)
        if col_name == "id":
            continue
        if not col_name.endswith("_id"):
            rename_map[col_name] = col_name + "_id"

    if not rename_map:
        return source

    # Apply renames - use word boundary to avoid partial matches
    for old_name, new_name in rename_map.items():
        source = re.sub(rf'\b{re.escape(old_name)}\b', new_name, source)

    return source


def main():
    model_files = []
    for path in sorted(DOMAINS_DIR.rglob("models/*.py")):
        if path.name == "__init__.py":
            continue
        if "read_models" in str(path):
            continue
        model_files.append(path)

    schema_fixed = 0
    fk_fixed = 0
    for path in model_files:
        domain = get_domain(path)
        if not domain:
            continue

        source = path.read_text(encoding="utf-8")
        if "__tablename__" not in source:
            continue

        new_source = source

        # Fix schema
        schema_result = fix_schema_in_file(new_source, domain)
        if schema_result != new_source:
            new_source = schema_result
            schema_fixed += 1

        # Fix FK columns
        fk_result = fix_fk_columns(new_source)
        if fk_result != new_source:
            new_source = fk_result
            fk_fixed += 1

        if new_source != source:
            path.write_text(new_source, encoding="utf-8")

    print(f"Schema fixes: {schema_fixed} files")
    print(f"FK column fixes: {fk_fixed} files")


if __name__ == "__main__":
    main()
