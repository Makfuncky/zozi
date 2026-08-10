import ast, pathlib
import importlib.util

spec = importlib.util.spec_from_file_location("fixw1", r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\fix_w1_writes.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

BACKEND = m.BACKEND
target = BACKEND / "routers" / "customer_wishlist_mgmt.py"
src = target.read_text(encoding="utf-8")
tree = ast.parse(src)
rw = m.Rewriter()
tree = rw.visit(tree)
ast.fix_missing_locations(tree)
if not m._already_imported(tree):
    m._add_import(tree)
out = ast.unparse(tree)
print("===== TRANSFORMED (dry run, not written) =====")
print(out)
print("===== counts =====")
print("changed:", rw.changed)
