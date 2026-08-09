"""Phase 2: Add schema declarations to all ORM models using AST."""
from __future__ import annotations

import ast
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BACKEND_DIR / "models"
SCHEMA_MAPPING_PATH = BACKEND_DIR / "docs" / "schema_mapping.json"


def load_schema_mapping() -> dict[str, str]:
    with SCHEMA_MAPPING_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)


SCHEMA_MAPPING = load_schema_mapping()


def add_schema_to_table_args(tree: ast.AST, schema: str) -> ast.AST:
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            tablename = None
            table_args = None
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            if target.id == "__tablename__" and isinstance(item.value, ast.Constant):
                                tablename = item.value.value
                            elif target.id == "__table_args__":
                                table_args = item.value

            if not tablename:
                continue

            table_schema = SCHEMA_MAPPING.get(tablename)
            if not table_schema or table_schema == "public" or table_schema != schema:
                continue

            if table_args is None:
                new_assign = ast.Assign(
                    targets=[ast.Name(id="__table_args__", ctx=ast.Load())],
                    value=ast.Constant(value={"schema": schema}),
                )
                insert_idx = None
                for i, item in enumerate(node.body):
                    if isinstance(item, ast.Assign):
                        for target in item.targets:
                            if isinstance(target, ast.Name) and target.id == "__tablename__":
                                insert_idx = i + 1
                                break
                    if insert_idx is not None:
                        break
                if insert_idx is not None:
                    node.body.insert(insert_idx, new_assign)
            else:
                if isinstance(table_args, ast.Tuple):
                    schema_dict = ast.Constant(value={"schema": schema})
                    table_args.elts.insert(0, schema_dict)
                elif isinstance(table_args, ast.Dict):
                    table_args.keys.append(ast.Constant(value="schema"))
                    table_args.values.append(ast.Constant(value=schema))
                elif isinstance(table_args, ast.Call):
                    pass
    return tree


def process_models() -> None:
    modified_files: set[str] = set()

    for py in sorted(MODELS_DIR.glob("*.py")):
        if py.name.startswith("_"):
            continue

        original = py.read_text(encoding="utf-8")

        try:
            tree = ast.parse(original)
        except SyntaxError as exc:
            print(f"[SKIP] {py.name}: {exc}")
            continue

        classes = [
            node for node in tree.body if isinstance(node, ast.ClassDef)
        ]

        modified = False
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

            has_schema = False
            for item in cls.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name) and target.id == "__table_args__":
                            if isinstance(item.value, ast.Tuple):
                                for elt in item.value.elts:
                                    if isinstance(elt, ast.Constant) and isinstance(elt.value, dict) and elt.value.get("schema") == schema:
                                        has_schema = True
                                        break
                            elif isinstance(item.value, ast.Dict):
                                for k, v in zip(item.value.keys, item.value.values):
                                    if isinstance(k, ast.Constant) and k.value == "schema" and isinstance(v, ast.Constant) and v.value == schema:
                                        has_schema = True
                                        break

            if has_schema:
                continue

            add_schema_to_table_args(cls, schema)
            modified = True

        if modified:
            try:
                new_source = ast.unparse(tree)
            except Exception as exc:
                print(f"[ERROR] Could not unparse {py.name}: {exc}")
                continue

            py.write_text(new_source, encoding="utf-8")
            modified_files.add(py.name)

    print(f"Modified {len(modified_files)} model files:")
    for name in sorted(modified_files):
        print(f"  {name}")


if __name__ == "__main__":
    process_models()
