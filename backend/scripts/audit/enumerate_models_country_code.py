import ast
import os
import json
from pathlib import Path

PROJECT_ROOT = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
MODEL_DIRS = [
    PROJECT_ROOT / "domains",
    PROJECT_ROOT / "infrastructure" / "database" / "models",
]

def is_orm_class(node, filepath):
    if not isinstance(node, ast.ClassDef):
        return False
    parts = list(filepath.parts)
    if "models" in parts:
        return True
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name) and target.id == "__tablename__":
                    return True
    for base in node.bases:
        name = ast.unparse(base)
        if name.endswith("Base"):
            return True
    return False

def find_model_files():
    files = []
    for d in MODEL_DIRS:
        if not d.exists():
            continue
        for f in d.rglob("*.py"):
            if f.name in {"base.py", "mixins.py", "__init__.py"}:
                continue
            files.append(f)
    return files

def analyze_file(filepath):
    try:
        source = filepath.read_text(encoding="utf-8")
    except Exception as e:
        return None, f"read error: {e}"
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return None, f"syntax error: {e}"

    classes = []
    for node in ast.walk(tree):
        if not is_orm_class(node, filepath):
            continue
        has_country_code = False
        country_code_line = None
        bases = [ast.unparse(b) for b in node.bases]
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "country_code":
                        has_country_code = True
                        country_code_line = item.lineno
                        break
        classes.append({
            "name": node.name,
            "lineno": node.lineno,
            "bases": bases,
            "has_country_code": has_country_code,
            "country_code_line": country_code_line,
        })
    return classes, None

def main():
    results = []
    missing = []
    present = []
    errors = []

    for f in sorted(find_model_files()):
        rel = str(f.relative_to(PROJECT_ROOT.parent))
        classes, err = analyze_file(f)
        if err:
            errors.append({"file": rel, "error": err})
            continue
        if not classes:
            continue
        for cls in classes:
            rec = {
                "file": rel,
                "class": cls["name"],
                "lineno": cls["lineno"],
                "bases": cls["bases"],
                "has_country_code": cls["has_country_code"],
                "country_code_line": cls["country_code_line"],
            }
            results.append(rec)
            if cls["has_country_code"]:
                present.append(rec)
            else:
                missing.append(rec)

    out = {
        "summary": {
            "total_classes": len(results),
            "with_country_code": len(present),
            "missing_country_code": len(missing),
            "errors": len(errors),
        },
        "missing": missing,
        "present": present,
        "errors": errors,
    }
    out_path = PROJECT_ROOT / "_audit_results" / "09_09_26" / "agent_17_country_scope_models.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Written to {out_path}")
    print(f"Total ORM classes: {len(results)}, missing country_code: {len(missing)}")
    if missing:
        print("Sample missing:")
        for m in missing[:30]:
            print(f"  {m['file']}:{m['lineno']} class {m['class']}")

if __name__ == "__main__":
    main()
