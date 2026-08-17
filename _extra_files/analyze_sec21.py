import ast, os, sys

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# The 14 TRUE-DUPLICATE groups from ARCHITECTURE_MIGRATION_REPORT.md section 2.1
# (function name + the two files the report cites)
PAIRS = [
    ("limit_bulk_size",        r"services\admin\admin_logistics_operations_service.py", r"services\core\admin_service.py"),
    ("connect_user",           r"services\comms\websocket_manager.py",                  r"services\public\public_comms_status_service.py"),
    ("connect_staff",          r"services\comms\websocket_manager.py",                  r"services\public\public_comms_status_service.py"),
    ("disconnect_user",        r"services\comms\websocket_manager.py",                  r"services\public\public_comms_status_service.py"),
    ("disconnect_staff",       r"services\comms\websocket_manager.py",                  r"services\public\public_comms_status_service.py"),
    ("broadcast_to_all_staff", r"services\comms\websocket_manager.py",                  r"services\public\public_comms_status_service.py"),
    ("get_session_country",    r"services\geography\cross_border_service.py",           r"services\geography\cross_border_tracker.py"),
    ("clear_session",          r"services\geography\cross_border_service.py",           r"services\geography\cross_border_tracker.py"),
    ("list_users",             r"controllers\admin\admin_identity_operations_api_controller.py", r"controllers\core\users_controller.py"),
    ("list_users",             r"controllers\admin\admin_identity_operations_api_controller.py", r"controllers\public\public_identity_operations_controller.py"),
    ("list_users",             r"controllers\core\users_controller.py",                r"controllers\public\public_identity_operations_controller.py"),
    ("scan_lookup_shipment",   r"controllers\core\logistics_partner_controller.py",     r"controllers\logistics\logistics_partner_verify_controller.py"),
    ("update_shipment_status",  r"controllers\core\logistics_partner_controller.py",     r"controllers\logistics\logistics_partner_verify_controller.py"),
    ("create_permission",       r"controllers\core\permissions_controller.py",          r"controllers\public\public_permissions_validation_controller.py"),
]

def parse(p):
    try:
        src = open(os.path.join(BACKEND, p.replace("\\", os.sep)), encoding="utf-8").read()
    except Exception as e:
        return None, None
    try:
        return src, ast.parse(src)
    except Exception:
        return src, None

def find_func(tree, name):
    """Return (node, enclosing_class_name) for the first FunctionDef/AsyncFunctionDef named `name`."""
    parent = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parent[c] = n
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            cur = parent.get(node)
            cls = None
            while cur is not None:
                if isinstance(cur, ast.ClassDef):
                    cls = cur.name
                    break
                cur = parent.get(cur)
            return node, cls
    return None, None

def imports_module(src, mod_dotted):
    """Heuristic: does src contain `from <mod_dotted> import` or `import <mod_dotted>`?"""
    import ast as _ast
    try:
        tree = _ast.parse(src)
    except Exception:
        return False
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            if n.module == mod_dotted or n.module.startswith(mod_dotted + "."):
                return True
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name == mod_dotted or a.name.startswith(mod_dotted + "."):
                    return True
    return False

def norm_dump(node):
    return ast.dump(node, include_attributes=False)

print("=== SECTION 2.1 PAIR ANALYSIS (function/method level) ===")
for i, (fn, a, b) in enumerate(PAIRS, 1):
    sa, ta = parse(a)
    sb, tb = parse(b)
    if ta is None: print(f"{i:>2} {fn:<22} PARSE_FAIL {a}"); continue
    if tb is None: print(f"{i:>2} {fn:<22} PARSE_FAIL {b}"); continue
    na, ca = find_func(ta, fn)
    nb, cb = find_func(tb, fn)
    if na is None or nb is None:
        print(f"{i:>2} {fn:<22} MISSING  A={a} found={na is not None} B={b} found={nb is not None}")
        continue
    identical = norm_dump(na) == norm_dump(nb)
    dec_a = [ast.unparse(d) for d in na.decorator_list]
    dec_b = [ast.unparse(d) for d in nb.decorator_list]
    async_a = isinstance(na, ast.AsyncFunctionDef)
    async_b = isinstance(nb, ast.AsyncFunctionDef)
    # import direction
    ma = a.replace("\\", ".").rsplit(".py", 1)[0]
    mb = b.replace("\\", ".").rsplit(".py", 1)[0]
    a_imp_b = imports_module(sa, mb)
    b_imp_a = imports_module(sb, ma)
    print(f"{i:>2} {fn:<22} ctxA={ca or 'MODULE':<18} ctxB={cb or 'MODULE':<18} "
          f"identical={identical} async={async_a or async_b} decA={dec_a} decB={dec_b} "
          f"impA->B={a_imp_b} impB->A={b_imp_a}")
