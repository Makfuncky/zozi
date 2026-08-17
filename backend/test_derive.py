import sys
sys.path.insert(0, ".")
from modules.routers.generated.auto_router import _derive_filename, scan_controllers

modules = scan_controllers()
for m in modules:
    if "admin_identity_operations_controller" in m["module"]:
        fname = _derive_filename(m["module"], m["routes"])
        print("Module:", m["module"])
        print("Filename:", fname)
        break
