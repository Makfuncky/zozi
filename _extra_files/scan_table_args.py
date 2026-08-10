import ast, pathlib
root = pathlib.Path("models")
bad = []
for f in sorted(root.rglob("*.py")):
    try:
        src = f.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception as e:
        print("PARSE FAIL", f, e); continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if isinstance(t, ast.Name) and t.id == "__table_args__":
                    val = node.value
                    if isinstance(val, (ast.Tuple, ast.List)):
                        elems = val.elts
                        dict_idxs = [i for i, e in enumerate(elems) if isinstance(e, ast.Dict)]
                        if dict_idxs and dict_idxs[-1] != len(elems) - 1:
                            bad.append((str(f), node.lineno, [type(e).__name__ for e in elems]))
print("TOTAL tuples with schema-dict not last:", len(bad))
for b in bad[:80]:
    print(b)
