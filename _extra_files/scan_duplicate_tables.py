import ast, os, collections
root = 'models'
tbl = collections.defaultdict(list)
for dirpath, _, files in os.walk(root):
    for f in files:
        if not f.endswith('.py'):
            continue
        p = os.path.join(dirpath, f)
        try:
            tree = ast.parse(open(p, encoding='utf-8').read())
        except Exception as e:
            print('PARSE ERR', p, e)
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for sub in ast.walk(node):
                    if isinstance(sub, ast.Assign):
                        for t in sub.targets:
                            if isinstance(t, ast.Name) and t.id == '__tablename__':
                                if isinstance(sub.value, ast.Constant):
                                    tbl[sub.value.value].append(
                                        f"{p}:{node.lineno} class {node.name}")
print("=== DUPLICATE TABLENAMES ===")
for t, loc in tbl.items():
    if len(loc) > 1:
        print(f"\n[{t}] ({len(loc)})")
        for l in loc:
            print("   ", l)
