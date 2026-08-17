import ast, os, sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# Each pair: (fileA_rel, fileB_rel, [qualified names], label)
# qualified name: "Func" (module-level) or "Class.method"
PAIRS = [
    ("services/comms/websocket_manager.py", "services/public/public_comms_status_service.py",
     ["UserConnectionManager.connect_user", "UserConnectionManager.connect_staff",
      "UserConnectionManager.disconnect_user", "UserConnectionManager.disconnect_staff",
      "UserConnectionManager.broadcast_to_all_staff"], "comms conn/staff methods"),
    ("services/geography/cross_border_service.py", "services/geography/cross_border_tracker.py",
     ["CrossBorderTracker.get_session_country", "CrossBorderTracker.clear_session"], "cross-border tracker methods"),
    ("controllers/admin/admin_identity_operations_api_controller.py", "controllers/core/users_controller.py",
     ["list_users"], "list_users A vs core"),
    ("controllers/admin/admin_identity_operations_api_controller.py", "controllers/public/public_identity_operations_controller.py",
     ["list_users"], "list_users A vs public"),
    ("controllers/core/users_controller.py", "controllers/public/public_identity_operations_controller.py",
     ["list_users"], "list_users core vs public"),
    ("controllers/core/logistics_partner_controller.py", "controllers/logistics/logistics_partner_verify_controller.py",
     ["scan_lookup_shipment", "update_shipment_status"], "logistics partner methods"),
    ("controllers/core/permissions_controller.py", "controllers/public/public_permissions_validation_controller.py",
     ["create_permission"], "create_permission"),
]

def load(path):
    src = open(path, encoding="utf-8").read()
    return src, ast.parse(src)

def find_def(tree, qname):
    """Return (node, kind) for a qualified name. kind in {'func','method'}."""
    if "." in qname:
        cls, meth = qname.split(".", 1)
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == cls:
                for sub in node.body:
                    if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name == meth:
                        return sub, "method"
        return None, None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == qname:
            # module-level preference
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # check if inside a class
                pass
    # module-level only
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == qname:
            return node, "func"
    return None, None

def class_dump(tree, clsname):
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == clsname:
            return ast.dump(node, include_attributes=False)
    return None

def dump_body(node):
    # body hash excluding decorators (compare logic)
    return ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)

print("=== Report §2.1 True Duplicate verification (AST body compare) ===\n")
for fa, fb, names, label in PAIRS:
    pa = os.path.join(BACKEND, fa)
    pb = os.path.join(BACKEND, fb)
    sa, ta = load(pa)
    sb, tb = load(pb)
    print(f"## {label}")
    print(f"   A: {fa}  B: {fb}")
    for q in names:
        na, ka = find_def(ta, q)
        nb, kb = find_def(tb, q)
        if na is None or nb is None:
            print(f"   - {q}: MISSING (A={na is not None}, B={nb is not None})")
            continue
        da = dump_body(na)
        db = dump_body(nb)
        same = da == db
        print(f"   - {q} [{ka}/{kb}]: {'IDENTICAL' if same else 'DIFFERENT'}")
        if not same:
            # show class-level identical?
            if "." in q:
                cls = q.split(".",1)[0]
                ca = class_dump(ta, cls); cb = class_dump(tb, cls)
                print(f"       Class {cls} identical? {'YES' if ca==cb else 'NO'}")
    print()

# Summarize class-level identity for the class-based pairs
print("=== Enclosing-class identity (for class-based dupes) ===")
for fa, fb, names, label in PAIRS[:2]:
    pa = os.path.join(BACKEND, fa); pb = os.path.join(BACKEND, fb)
    sa, ta = load(pa); sb, tb = load(pb)
    classes = set()
    for n in names:
        if "." in n:
            classes.add(n.split(".",1)[0])
    for cls in sorted(classes):
        ca = class_dump(ta, cls); cb = class_dump(tb, cls)
        print(f"  {cls}: {'WHOLE-CLASS IDENTICAL' if ca==cb else 'CLASSES DIFFER'}  ({fa} <-> {fb})")
