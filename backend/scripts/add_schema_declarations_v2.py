"""Phase 2: Add schema declarations to all ORM models.

Uses a line-based parser to safely insert {"schema": "..."} into
__table_args__ tuples without breaking formatting.
"""
from __future__ import annotations

import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def add_schema_to_table_args(source: str, table_name: str, schema: str) -> str:
    if schema == "public":
        return source

    if f'"schema": "{schema}"' in source or "'schema': '" + schema + "'" in source:
        return source

    lines = source.splitlines(keepends=True)
    result = []
    i = 0
    modified = False

    while i < len(lines):
        line = lines[i]

        if not modified and line.strip() == f'__tablename__ = "{table_name}"':
            result.append(line)
            i += 1

            # Skip empty lines after tablename
            while i < len(lines) and not lines[i].strip():
                result.append(lines[i])
                i += 1

            if i < len(lines) and lines[i].strip().startswith("__table_args__"):
                # Existing __table_args__
                result.append(lines[i])
                i += 1

                # Collect the tuple content
                tuple_lines = []
                depth = 0
                while i < len(lines):
                    current = lines[i]
                    depth += current.count("(") - current.count(")")
                    tuple_lines.append(current)
                    i += 1
                    if depth <= 0 and current.strip().endswith(")"):
                        break

                # Check if schema is already present
                tuple_text = "".join(tuple_lines)
                if f'"schema": "{schema}"' not in tuple_text and "'schema': '" + schema + "'" not in tuple_text:
                    # Insert schema dict before the closing )
                    if tuple_lines:
                        closing_line = tuple_lines[-1]
                        indent = len(closing_line) - len(closing_line.lstrip())
                        schema_line = " " * indent + '{"schema": "' + schema + '"},\n'
                        tuple_lines.insert(-1, schema_line)
                        modified = True
                result.extend(tuple_lines)
            else:
                # No __table_args__, add one
                indent = "    "
                result.append(f"{indent}__table_args__ = " + '{"schema": "' + schema + '"}\n')
                modified = True
            continue

        result.append(line)
        i += 1

    return "".join(result)


def process_models() -> None:
    modified_files = []

    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        original = py.read_text(encoding="utf-8")
        updated = original

        try:
            tree = ast.parse(original)
        except SyntaxError as exc:
            print(f"[SKIP] {py.name}: {exc}")
            continue

        classes = [
            node for node in tree.body if isinstance(node, ast.ClassDef)
        ]

        for cls in classes:
            tablename = None
            for item in cls.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__tablename__":
                            if isinstance(item.value, ast.Constant) and isinstance(item.value.value, str):
                                tablename = item.value.value

            if not tablename:
                continue

            schema = SCHEMA_MAPPING.get(tablename)
            if not schema or schema == "public":
                continue

            updated = add_schema_to_table_args(updated, tablename, schema)

        if updated != original:
            py.write_text(updated, encoding="utf-8")
            modified_files.append(py.name)

    print(f"Modified {len(modified_files)} model files:")
    for name in sorted(modified_files):
        print(f"  {name}")


if __name__ == "__main__":
    import ast
    process_models()
