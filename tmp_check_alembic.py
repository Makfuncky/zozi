import ast, os

versions_dir = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\alembic\versions"
revisions = {}
for fn in sorted(os.listdir(versions_dir)):
    if not fn.endswith(".py") or fn in ("__init__.py",):
        continue
    path = os.path.join(versions_dir, fn)
    tree = ast.parse(open(path, encoding="utf-8").read())
    rev = down = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "revision":
                        rev = ast.literal_eval(node.value)
                    elif target.id == "down_revision":
                        if isinstance(node.value, ast.Constant) and node.value.value is not None:
                            down = node.value.value
    if rev is not None:
        revisions.setdefault(rev, []).append(fn)

for rev, fns in sorted(revisions.items()):
    marker = "  <-- DUPLICATE" if len(fns) > 1 else ""
    print(f"{rev:25} -> {', '.join(fns)}{marker}")