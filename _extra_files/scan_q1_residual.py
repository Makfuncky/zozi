"""Read-only residual Q1 scan: count literal db.query/db.execute in layers."""
import ast, pathlib

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
LAYER_DIRS = (BACKEND / "routers", BACKEND / "controllers", BACKEND / "middleware")
SESSION_NAMES = {"db","session","sess","db_session","_db","_session","_db_session","_sess"}
READ_ATTRS = {"query","execute"}

found = []
for layer in LAYER_DIRS:
    if not layer.exists():
        continue
    for path in sorted(layer.rglob("*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                v = node.func.value
                if isinstance(v, ast.Name) and v.id in SESSION_NAMES and node.func.attr in READ_ATTRS:
                    found.append((str(path.relative_to(BACKEND)), node.lineno, f"{v.id}.{node.func.attr}"))

print(f"residual Q1 sites = {len(found)}")
for f, ln, c in found[:50]:
    print(f"  {f}:{ln}  {c}")
