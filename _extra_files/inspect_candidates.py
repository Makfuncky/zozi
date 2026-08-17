"""Inspect candidate duplicate functions: method status, decorators, async, circular risk."""
import ast, os

BACKEND = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"

pairs = [
 ("services/admin/admin_logistics_operations_service.py","admin_logistics_overview"),
 ("services/core/admin_service.py","admin_logistics_overview"),
 ("services/commerce/coupons_read_service.py","get_coupon_usage_count"),
 ("services/commerce/coupons_write_service.py","get_coupon_usage_count"),
 ("services/geography/country_write_service.py","add_to_session"),
 ("services/supplier/suppliers_write_service.py","add_to_session"),
 ("services/hr/learning_write_service.py","create_training_module"),
 ("services/hr/lms_service.py","create_training_module"),
 ("services/hr/learning_write_service.py","assign_training"),
 ("services/hr/lms_service.py","assign_training"),
 ("services/public/public_comms_status_service.py","websocket_chat"),
 ("services/public/system_comms_status_service.py","websocket_chat"),
 ("services/public/system_ai_upload_service.py","process_ai_upload_job"),
 ("services/system/system_ai_upload_service.py","process_ai_upload_job"),
 ("services/treasury/treasury_query_service.py","get_treasury_metrics"),
 ("services/treasury/treasury_service.py","get_treasury_metrics"),
]

def enclosing_class(tree, node):
    for parent in ast.walk(tree):
        for sub in ast.iter_child_nodes(parent):
            if sub is node and isinstance(parent, ast.ClassDef):
                return parent.name
    return None

def module_imports_of(tree):
    mods=set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.add(n.module)
        elif isinstance(n, ast.Import):
            for a in n.names:
                mods.add(a.name)
    return mods

for fp,name in pairs:
    full=os.path.join(BACKEND,fp)
    try:
        src=open(full,encoding="utf-8").read()
        t=ast.parse(src)
    except Exception as e:
        print(f"!! {fp}: PARSE ERR {e}"); continue
    found=None
    for node in ast.walk(t):
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name==name:
            found=node; break
    if not found:
        print(f"-- {fp}:{name} NOT FOUND"); continue
    cls=enclosing_class(t,found)
    decs=[ast.unparse(d) for d in found.decorator_list]
    imps=module_imports_of(t)
    in_all = "__all__" in src and name in src.split("__all__")[1][:200] if "__all__" in src else False
    print(f"== {fp}:{name} method={cls} async={isinstance(found,ast.AsyncFunctionDef)} decs={decs} in__all~={in_all}")
    print(f"     imports={sorted(imps)[:8]}")
