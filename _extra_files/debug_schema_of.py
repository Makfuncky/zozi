import ast, pathlib
f = pathlib.Path("models/comms/core.py")
tree = ast.parse(f.read_text(encoding="utf-8"))
for cls in ast.walk(tree):
    if not isinstance(cls, ast.ClassDef) or cls.name != "Address": continue
    for n in cls.body:
        if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "__table_args__" for t in n.targets):
            v = n.value
            print("v type", type(v).__name__, "has elems attr:", hasattr(v, "elems"))
            elems = getattr(v, "elems", None)
            print("elems", elems)
            if elems:
                for e in elems:
                    print(" elem", type(e).__name__, "isDict", isinstance(e, ast.Dict))
                    if isinstance(e, ast.Dict):
                        print("  keys", [type(k).__name__ for k in e.keys], [getattr(k,'value',None) for k in e.keys])
                        for k, val in zip(e.keys, e.values):
                            print("   k", repr(k), "val", repr(val))
