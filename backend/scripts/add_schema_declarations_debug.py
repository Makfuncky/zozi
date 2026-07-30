"""Phase 2: Add schema declarations to all ORM models."""
from __future__ import annotations

import ast
import json
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def ensure_schema_in_table_args(source: str, table_name: str, schema: str) -> str:
    if schema == "public":
        return source

    if '"schema"' in source or "'schema'" in source:
        return source

    tablename_pattern = re.compile(
        r'(__tablename__\s*=\s*"'
        + re.escape(table_name)
        + r'")',
        re.MULTILINE,
    )
    match = tablename_pattern.search(source)
    if not match:
        return source

    start = match.start()
    lines_after = source[match.end():].splitlines(keepends=True)
    insert_point = match.end()

    consumed = 0
    found_table_args = False
    for line in lines_after:
        stripped = line.strip()
        if stripped.startswith("__table_args__"):
            found_table_args = True
            break
        if stripped and not stripped.startswith("#") and not stripped.startswith('"""') and not stripped.startswith("'''"):
            break
        consumed += len(line)
        if consumed > 400:
            break

    if found_table_args:
        args_pattern = re.compile(
            r"(__table_args__\s*=\s*\()(\s*)(.*?)(\s*)\)",
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
        if count > 0:
            return new_source

        dict_pattern = re.compile(
            r"(__table_args__\s*=\s*\{)(.*?)(\s*\})",
            re.DOTALL,
        )
        new_source, count = dict_pattern.subn(
            lambda m, s=schema: m.group(1)
            + m.group(2).rstrip()
            + ', "schema": "'
            + s
            + '"'
            + m.group(3),
            source,
        )
        if count > 0:
            return new_source

        return source

    insert_text = (
        f'\n    __table_args__ = {{"schema": "{schema}"}}\n'
    )
    return source[:insert_point] + insert_text + source[insert_point:]


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

            if f'"schema": "{schema}"' in updated or f"'schema': '{schema}'" in updated:
                continue

            updated = ensure_schema_in_table_args(updated, tablename, schema)

        if updated != original:
            py.write_text(updated, encoding="utf-8")
            modified_files.append(py.name)
            print(f"Modified: {py.name}")
        else:
            print(f"Unchanged: {py.name}")

    print(f"\nTotal modified: {len(modified_files)}")


if __name__ == "__main__":
    process_models()
