import ast, os, sys, importlib.util, traceback

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# (func, fileA, fileB) from ARCHITECTURE_MIGRATION_REPORT.md section 2.1
PAIRS = [
    ("limit_bulk_size", r"services\admin\admin_logistics_operations_service.py", r"services\core\admin_service.py"),
    ("connect_user", r"services\comms\websocket_manager.py", r"services\public\public_comms_status_service.py"),
    ("connect_user", r"services\comms\websocket_manager.py", r"services\public\system_comms_status_service.py"),
    ("connect_user", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("connect_staff", r"services\comms\websocket_manager.py", r"services\public\public_comms_status_service.py"),
    ("connect_staff", r"services\comms\websocket_manager.py", r"services\public\system_comms_status_service.py"),
    ("connect_staff", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("disconnect_user", r"services\comms\websocket_manager.py", r"services\public\public_comms_status_service.py"),
    ("disconnect_user", r"services\comms\websocket_manager.py", r"services\public\system_comms_status_service.py"),
    ("disconnect_user", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("disconnect_staff", r"services\comms\websocket_manager.py", r"services\public\public_comms_status_service.py"),
    ("disconnect_staff", r"services\comms\websocket_manager.py", r"services\public\system_comms_status_service.py"),
    ("disconnect_staff", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("broadcast_to_all_staff", r"services\comms\websocket_manager.py", r"services\public\public_comms_status_service.py"),
    ("broadcast_to_all_staff", r"services\comms\websocket_manager.py", r"services\public\system_comms_status_service.py"),
    ("broadcast_to_all_staff", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("check_in", r"services\employee\attendance_service.py", r"services\hr\attendance_service.py"),
    ("check_out", r"services\employee\attendance_service.py", r"services\hr\attendance_service.py"),
    ("get_daily_attendance", r"services\employee\attendance_service.py", r"services\hr\attendance_service.py"),
    ("detect_late_arrival", r"services\employee\attendance_service.py", r"services\hr\attendance_service.py"),
    ("to_dict", r"services\employee\background_check.py", r"services\hr\background_check.py"),
    ("get_session_country", r"services\geography\cross_border_service.py", r"services\geography\cross_border_tracker.py"),
    ("clear_session", r"services\geography\cross_border_service.py", r"services\geography\cross_border_tracker.py"),
    ("connect", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("disconnect", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("broadcast", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("set_typing", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("get_typing_users", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("get_room_users", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("get_room_size", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("broadcast_to_user", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("broadcast_to_staff", r"services\public\public_comms_status_service.py", r"services\public\system_comms_status_service.py"),
    ("list_users", r"controllers\admin\admin_identity_operations_api_controller.py", r"controllers\core\users_controller.py"),
    ("list_users", r"controllers\admin\admin_identity_operations_api_controller.py", r"controllers\public\public_identity_operations_controller.py"),
    ("list_users", r"controllers\core\users_controller.py", r"controllers\public\public_identity_operations_controller.py"),
    ("scan_lookup_shipment", r"controllers\core\logistics_partner_controller.py", r"controllers\logistics\logistics_partner_verify_controller.py"),
    ("update_shipment_status", r"controllers\core\logistics_partner_controller.py", r"controllers\logistics\logistics_partner_verify_controller.py"),
    ("create_permission", r"controllers\core\permissions_controller.py", r"controllers\public\public_permissions_validation_controller.py"),
]

def mod_path(rel):
    return os.path.join(BACKEND, rel.replace("\\", os.sep))

def find_func(filepath, name):
    """Return (node, context) where context in {'module','class'}; handles sync+async."""
    try:
        src = open(filepath, encoding="utf-8").read()
    except Exception as e:
        return None
    try:
        tree = ast.parse(src)
    except Exception:
        return None
    # build parent map
    parent = {tree: None}
    for n in ast.walk(tree):
        for child in ast.iter_child_nodes(n):
            parent[child] = n
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            cur = parent.get(node)
            is_method = False
            while cur is not None:
                if isinstance(cur, ast.ClassDef):
                    is_method = True
                    break
                cur = parent.get(cur)
            return (node, "class" if is_method else "module")
    return None

def norm_src(node):
    # re-generate source minus decorators, trimmed whitespace
    body_src = ast.dump(node, include_attributes=False)
    return body_src

def has_decorators(node):
    return len(node.decorator_list) > 0

def module_imports_ok(rel):
    mod = rel.replace("\\", "/").replace("/", ".").rsplit(".py",1)[0]
    # strip leading backend? it is already backend/services... we pass absolute path; build module name from backend root
    relmod = rel.replace("\\","/").rsplit(".py",1)[0]
    full = "backend." + relmod
    try:
        importlib.import_module(full)
        return True, ""
    except Exception as e:
        return False, f"{type(e).__name__}: {str(e)[:120]}"

print(f"{'#':>2} {'FUNC':<24} {'A':<40} {'B':<40} CTX_A CTX_B DEC_A DEC_B IDENT  CANON_OK  DECISION")
results = []
for i,(func,a,b) in enumerate(PAIRS,1):
    pa, pb = mod_path(a), mod_path(b)
    ra, rb = find_func(pa, func), find_func(pb, func)
    na = ra[0] if ra else None; ca_ctx = ra[1] if ra else "?"
    nb = rb[0] if rb else None; cb_ctx = rb[1] if rb else "?"
    da = has_decorators(na) if na else None
    db = has_decorators(nb) if nb else None
    ident = "?"
    if na and nb:
        ident = "Y" if norm_src(na)==norm_src(nb) else "N"
    ca_ok, ca_err = module_imports_ok(a)
    cb_ok, cb_err = module_imports_ok(b)
    # decision
    if not na or not nb:
        dec = "NOT_FOUND"
    elif ca_ctx == "class" or cb_ctx == "class":
        dec = "UNSAFE_METHOD"
    elif da or db:
        dec = "UNSAFE_DECORATED"
    elif ident != "Y":
        dec = "UNSAFE_NOT_IDENTICAL"
    else:
        # pick canonical that imports OK; prefer first
        if ca_ok:
            dec = "SAFE_SHIM <-A"
            canon = a
        elif cb_ok:
            dec = "SAFE_SHIM <-B"
            canon = b
        else:
            dec = "CANON_BROKEN"
    results.append((i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err))
    print(f"{i:>2} {func:<24} {os.path.basename(a):<40} {os.path.basename(b):<40} {ca_ctx:<5} {cb_ctx:<5} {str(da):<5} {str(db):<5} {ident:<6} {str(ca_ok):<7} {dec}")

print()
print("=== grouped by decision ===")
from collections import Counter, defaultdict
c = Counter(r[11] for r in results)
for k,v in c.items():
    print(f"{k}: {v}")
print()
print("=== SAFE_SHIM details (canonical candidates) ===")
for r in results:
    if r[11].startswith("SAFE_SHIM"):
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        canon = a if ca_ok else b
        print(f"{i:>2} {func:<24} A={os.path.basename(a)} B={os.path.basename(b)} -> canonical={os.path.basename(canon)} ({dec})")
print()
print("=== CANON_BROKEN ===")
for r in results:
    if r[11]=="CANON_BROKEN":
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        print(f"{i:>2} {func:<24} A={a} [{ca_err}]  B={b} [{cb_err}]")
print()
print("=== UNSAFE_DECORATED ===")
for r in results:
    if r[11]=="UNSAFE_DECORATED":
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        print(f"{i:>2} {func:<24} A={os.path.basename(a)} decA={da} B={os.path.basename(b)} decB={db}")
print()
print("=== UNSAFE_METHOD ===")
for r in results:
    if r[11]=="UNSAFE_METHOD":
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        print(f"{i:>2} {func:<24} A={os.path.basename(a)} ctxA={ca_ctx} B={os.path.basename(b)} ctxB={cb_ctx}")
print()
print("=== UNSAFE_NOT_IDENTICAL ===")
for r in results:
    if r[11]=="UNSAFE_NOT_IDENTICAL":
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        print(f"{i:>2} {func:<24} A={os.path.basename(a)} B={os.path.basename(b)}")
print()
print("=== NOT_FOUND ===")
for r in results:
    if r[11]=="NOT_FOUND":
        i,func,a,b,ca_ctx,cb_ctx,da,db,ident,ca_ok,cb_ok,dec,ca_err,cb_err = r
        print(f"{i:>2} {func:<24} A={os.path.basename(a)} B={os.path.basename(b)}")
