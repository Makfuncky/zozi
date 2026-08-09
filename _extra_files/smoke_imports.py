import os, sys
sys.path.insert(0, r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
# core module smoke
import models, data.models, db, utils
print("core modules OK")
# try importing the app entry / routers to ensure import graph is healthy
import importlib
for m in ["main", "routers.admin_core_console", "controllers.admin_controller", "services"]:
    try:
        importlib.import_module(m)
        print("import OK:", m)
    except Exception as e:
        print("import FAIL:", m, "->", type(e).__name__, str(e)[:200])
