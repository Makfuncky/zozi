import ast, os

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
WRITE_VERBS = {"add","add_all","commit","delete","flush","merge","refresh","begin","begin_nested","savepoint","bulk_insert_mappings","bulk_save_objects","bulk_update_mappings"}
READ_ATTRS = {"query","execute"}

layers = {"routers": [], "controllers": [], "middleware": []}
for layer in layers:
    d = os.path.join(BACKEND, layer)
    if not os.path.isdir(d):
        continue
    for f in sorted(os.listdir(d)):
        if not f.endswith(".py") or f.startswith("__"):
            continue
        p = os.path.join(d, f)
        try:
            src = open(p, encoding="utf-8").read()
        except Exception:
            continue
        try:
            tree = ast.parse(src)
        except SyntaxError:
            print("PARSE FAIL", p)
            continue
        writes = []
        reads = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                recv = node.func.value
                name = recv.id if isinstance(recv, ast.Name) else (recv.attr if isinstance(recv, ast.Attribute) else None)
                if name == "db" and node.func.attr in WRITE_VERBS:
                    writes.append("L%d:%s.%s" % (node.lineno, name, node.func.attr))
                if name == "db" and node.func.attr in READ_ATTRS:
                    reads.append("L%d:%s.%s" % (node.lineno, name, node.func.attr))
        if writes or reads:
            layers[layer].append((f, len(writes), len(reads), writes[:8], reads[:8]))

total_w = total_r = 0
for layer, items in layers.items():
    print("\n=== %s: %d files with db access ===" % (layer, len(items)))
    for f, nw, nr, w, r in items:
        total_w += nw
        total_r += nr
        print("  %s: W1=%d Q1=%d  %s %s" % (f, nw, nr, w, r))
print("\nTOTAL writes=%d reads=%d" % (total_w, total_r))
