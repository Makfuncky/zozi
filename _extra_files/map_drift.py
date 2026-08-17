import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
import importlib.util
spec = importlib.util.spec_from_file_location("auto_router", r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\routers\generated\auto_router.py")
ar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ar)

targets = ["admin_logistics_operations.py","admin_security_detection.py","public_core_admin.py","public_customer_coupons_create.py","public_security_detection.py"]

mods = ar.scan_controllers()
# map filename -> module
fname_to_mod = {}
for mi in mods:
    fn = ar._derive_filename(mi["module"], mi["routes"])
    fname_to_mod.setdefault(fn, []).append(mi["module"])

for t in targets:
    print("===", t, "==>")
    print("  modules producing it:", fname_to_mod.get(t, []))
    # find the module and regenerate
    for mi in mods:
        if ar._derive_filename(mi["module"], mi["routes"]) == t:
            # regenerate content
            content = ar.generate_router_file(mi)
            disk = open(os.path.join(ar.DEFAULT_OUT, t), encoding="utf-8").read()
            print("  len on-disk:", len(disk), " len regen:", len(content), " equal:", disk==content)
