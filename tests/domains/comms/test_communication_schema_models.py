import ast

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MODEL_FILE = REPO_ROOT / "backend" / "domains" / "comms" / "models" / "communication_schema_models.py"

REQUIRED_COLUMNS = {"updated_at", "is_deleted"}
TARGET_MODELS = {"SupportTicketReply", "NewsSource", "InternalNotice", "EscalationSLARule"}


def _get_model_columns(source: str):
    tree = ast.parse(source)
    columns = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_cols = set()
            for item in node.body:
                if isinstance(item, ast.Assign):
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            class_cols.add(target.id)
            columns[node.name] = class_cols
    return columns


def test_all_models_have_updated_at_and_is_deleted():
    source = MODEL_FILE.read_text(encoding="utf-8")
    model_columns = _get_model_columns(source)

    for model_name in TARGET_MODELS:
        assert model_name in model_columns, f"Model {model_name} not found in file"
        missing = REQUIRED_COLUMNS - model_columns[model_name]
        assert not missing, f"{model_name} missing columns: {missing}"


def test_fk_columns_have_index():
    source = MODEL_FILE.read_text(encoding="utf-8")
    tree = ast.parse(source)
    fk_columns_missing_index = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "ForeignKey":
                parent = None
                for sibling in ast.walk(tree):
                    pass
                for item in ast.walk(ast.Module(body=[node], type_ignores=[])):
                    pass
                for stmt in ast.walk(tree):
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                for kw in node.keywords:
                                    if kw.arg == "ondelete":
                                        break
                                else:
                                    if stmt.value == node:
                                        if not any(
                                            kw.arg == "index" and kw.value.value is True
                                            for kw in stmt.value.keywords
                                            if isinstance(kw.value, ast.Constant)
                                        ):
                                            fk_columns_missing_index.append(ast.unparse(node))

    assert not fk_columns_missing_index, (
        "ForeignKey columns missing index=True: "
        + ", ".join(fk_columns_missing_index)
    )
