import re
p = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\scripts\rewrite_imports.py"
s = open(p, encoding="utf-8").read()

new_func = '''def rewrite_source(src):
    tree = ast.parse(src)
    notes = []
    edits = []

    class Visitor(ast.NodeVisitor):
        def visit_ImportFrom(self, node):
            new_mod, note = _rewrite_module(node.module)
            if new_mod is not None and new_mod != node.module:
                node.module = new_mod
                notes.append("L%d: from %s -> %s" % (node.lineno, node.module, new_mod))
                edits.append((node, None))
            self.generic_visit(node)

        def visit_Import(self, node):
            changed = False
            for alias in node.names:
                if alias.name in ("models", "db") and (alias.asname is None or alias.asname == alias.name):
                    orig = alias.name
                    new_name = "_legacy." + orig
                    alias.name = new_name
                    alias.asname = orig
                    notes.append("L%d: import %s -> import %s as %s" % (node.lineno, orig, new_name, orig))
                    changed = True
            if changed:
                edits.append((node, None))
            self.generic_visit(node)

    Visitor().visit(tree)
    if not edits:
        return src, notes
    lines = src.splitlines(keepends=True)
    for node, _ in edits:
        ln = node.lineno - 1
        lines[ln] = ast.unparse(node) + chr(10)
    return "".join(lines), notes
'''

pattern = r'def rewrite_source\(src\):.*?\ndef _has_legacy\(src\):'
assert re.search(pattern, s, re.DOTALL), "rewrite_source not found"
s = re.sub(pattern, new_func + "def _has_legacy(src):", s, count=1, flags=re.DOTALL)

open(p, "w", encoding="utf-8").write(s)
print("rewrite_source rebuilt (ast.unparse, multi-line safe)")
