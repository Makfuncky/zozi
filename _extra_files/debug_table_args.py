import ast, pathlib
f = pathlib.Path("models/comms/core.py")
tree = ast.parse(f.read_text(encoding="utf-8"))
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef): continue
    if cls.name != "Address": continue
    for n in cls.body:
        if isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name) and t.id == "__table_args__":
                    print("TARGET_TYPE", type(n).__name__)
                    print("VALUE_TYPE", type(n.value).__name__)
                    elems = getattr(n.value, "elts", None)
                    print("ELEMS", elems is not None, len(elems) if elems else 0)
                    for e in (elems or []):
                        print("  ", type(e).__name__, isinstance(e, ast.Dict))
