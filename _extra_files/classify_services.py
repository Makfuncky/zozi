import ast
import os
from pathlib import Path
from collections import defaultdict

BACKEND = Path(__file__).resolve().parent.parent / "backend"
SERVICES_DIR = BACKEND / "services"

PROVIDER_NAME_PREFIXES = ("require_", "get_current_", "_require")

def classify_service_file(path: Path):
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return "unreadable"
    
    stripped = source.strip()
    if not stripped:
        return "empty"
    
    # Count actual code lines (non-comment, non-blank)
    lines = source.splitlines()
    non_comment_lines = [l for l in lines if l.strip() and not l.strip().startswith("#")]
    if not non_comment_lines:
        return "empty"
    
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return "stub"
    
    # Count top-level statements that are not imports/docstrings
    top_level_funcs = 0
    top_level_classes = 0
    has_non_import_stmt = False
    has_public_func = False
    
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            top_level_classes += 1
            has_public_func = True
            has_non_import_stmt = True
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            top_level_funcs += 1
            has_public_func = True
            has_non_import_stmt = True
        elif isinstance(node, ast.Assign):
            has_non_import_stmt = True
        elif isinstance(node, ast.AnnAssign):
            has_non_import_stmt = True
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            pass
        elif isinstance(node, ast.Expr):
            if isinstance(node.value, (ast.Str, ast.Constant)):
                pass
            else:
                has_non_import_stmt = True
        else:
            has_non_import_stmt = True
    
    # Pure re-export shim: only imports + optional __all__ + docstrings
    all_are_imports_or_docstrings = True
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        elif isinstance(node, ast.Expr):
            if isinstance(node.value, (ast.Str, ast.Constant)):
                continue
            all_are_imports_or_docstrings = False
            break
        elif isinstance(node, ast.Assign):
            if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and node.targets[0].id == "__all__":
                continue
            all_are_imports_or_docstrings = False
            break
        else:
            all_are_imports_or_docstrings = False
            break
    
    if all_are_imports_or_docstrings and (top_level_funcs > 0 or top_level_classes > 0):
        return "reexport"
    
    if not has_non_import_stmt:
        return "stub"
    
    return "valid"

results = defaultdict(list)
for py_file in sorted(SERVICES_DIR.rglob("*.py")):
    if "__pycache__" in str(py_file):
        continue
    if py_file.name == "__init__.py":
        continue
    if py_file.name.startswith("__"):
        continue
    
    category = classify_service_file(py_file)
    rel = str(py_file.relative_to(BACKEND))
    results[category].append(rel)

for cat in ["empty", "reexport", "stub", "valid"]:
    files = results[cat]
    print(f"\n=== {cat.upper()} ({len(files)}) ===")
    for f in files:
        print(f"  {f}")

print(f"\n=== SUMMARY ===")
print(f"Empty: {len(results['empty'])}")
print(f"Re-export: {len(results['reexport'])}")
print(f"Stub: {len(results['stub'])}")
print(f"Valid: {len(results['valid'])}")
print(f"Total to remove: {len(results['empty']) + len(results['reexport']) + len(results['stub'])}")
print(f"Total: {sum(len(v) for v in results.values())}")
