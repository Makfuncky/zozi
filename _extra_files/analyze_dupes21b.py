import ast, os, sys, importlib.util
from collections import defaultdict

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

# All files referenced in section 2.1
FILES = [
    r"services\admin\admin_logistics_operations_service.py",
    r"services\core\admin_service.py",
    r"services\comms\websocket_manager.py",
    r"services\public\public_comms_status_service.py",
    r"services\public\system_comms_status_service.py",
    r"services\employee\attendance_service.py",
    r"services\hr\attendance_service.py",
    r"services\employee\background_check.py",
    r"services\hr\background_check.py",
    r"services\geography\cross_border_service.py",
    r"services\geography\cross_border_tracker.py",
    r"controllers\admin\admin_identity_operations_api_controller.py",
    r"controllers\core\users_controller.py",
    r"controllers\public\public_identity_operations_controller.py",
    r"controllers\core\logistics_partner_controller.py",
    r"controllers\logistics\logistics_partner_verify_controller.py",
    r"controllers\core\permissions_controller.py",
    r"controllers\public\public_permissions_validation_controller.py",
]

def abs(p): return os.path.join(BACKEND, p.replace("\\", os.sep))

def parse(p):
    try:
        src = open(p, encoding="utf-8").read()
    except Exception:
        return None, None
    try:
        tree = ast.parse(src)
    except Exception:
        return None, None
    return src, tree

# index: top-level classes and module-level functions per file
classes = defaultdict(list)   # key=ast.dump(classnode) -> list of (file, classname)
funcs   = defaultdict(list)   # key=ast.dump(funcnode)  -> list of (file, funcname)
class_key_for_func = {}       # (file,funcname) -> enclosing class name

for f in FILES:
    src, tree = parse(abs(f))
    if tree is None:
        print(f"!! cannot parse {f}")
        continue
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            classes[ast.dump(node, include_attributes=False)].append((f, node.name))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # module-level function (decorator-free = pure duplicate candidate)
            key = ast.dump(node, include_attributes=False)
            funcs[key].append((f, node.name))

print("===== DUPLICATE TOP-LEVEL CLASSES (byte-identical) =====")
dup_classes = {k:v for k,v in classes.items() if len(v) > 1}
for k, v in dup_classes.items():
    names = sorted(set(n for _,n in v))
    files = sorted(set(os.path.basename(f) for f,_ in v))
    print(f"  class {names}  in {files}  (count={len(v)})")

print()
print("===== DUPLICATE MODULE-LEVEL FUNCTIONS (byte-identical, decorator-free) =====")
dup_funcs = {k:v for k,v in funcs.items() if len(v) > 1}
for k, v in dup_funcs.items():
    names = sorted(set(n for _,n in v))
    files = sorted(set(os.path.basename(f) for f,_ in v))
    print(f"  func {names}  in {files}  (count={len(v)})")

# Now map the section 2.1 pairs to whether they belong to a duplicate class or dup func
print()
print("===== SECTION 2.1 PAIR RESOLUTION =====")
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

def enclosing_class(f, funcname):
    src, tree = parse(abs(f))
    if tree is None: return None
    parent = {}
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            parent[c] = n
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == funcname:
            cur = parent.get(node)
            while cur is not None:
                if isinstance(cur, ast.ClassDef):
                    return cur.name
                cur = parent.get(cur)
            return None
    return None

for i,(func,a,b) in enumerate(PAIRS,1):
    ca = enclosing_class(a, func)
    cb = enclosing_class(b, func)
    # check if (a,ca) and (b,cb) are in dup_classes
    verdict = "?"
    if ca is not None and cb is not None and ca == cb:
        # find matching dup class entry
        found = None
        for k,v in dup_classes.items():
            names = set(n for _,n in v)
            files = set(f for f,_ in v)
            if ca in names and os.path.basename(a) in set(os.path.basename(x) for x in files) and os.path.basename(b) in set(os.path.basename(x) for x in files):
                found = (ca, sorted(set(os.path.basename(x) for x in files)))
                break
        if found:
            verdict = f"SAFE_CLASS_REEXPORT (class {found[0]} in {found[1]})"
        else:
            verdict = f"PARTIAL_CLASS (class {ca} differs between files)"
    elif ca is None and cb is None:
        verdict = "MODULE_FUNC (check dup_funcs)"
    else:
        verdict = f"MISMATCH ctx: A={ca} B={cb}"
    print(f"{i:>2} {func:<22} A={os.path.basename(a):<42} B={os.path.basename(b):<42} -> {verdict}")
