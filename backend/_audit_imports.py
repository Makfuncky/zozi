import importlib, traceback, sys
mods = [
 "config","lifespan","main",
 "kernel","kernel.money","kernel.numbering","kernel.country","kernel.currency","kernel.period",
 "rbac","rbac.catalog","rbac.resolution","rbac.dependencies","rbac.roles","rbac.service","rbac.models",
 "infrastructure","infrastructure.database.database","infrastructure.database.base","infrastructure.database.session",
 "infrastructure.utils.config","infrastructure.utils.versioning","infrastructure.redis",
 "middleware.orchestrator",
]
# all module router packages
import os
for m in ["customer","supplier","logistics","admin","employee","commerce","products"]:
    mods.append(f"modules.{m}.routers")
# all domains
for d in sorted(os.listdir("domains")):
    if os.path.isdir(os.path.join("domains",d)) and not d.startswith("__"):
        mods.append(f"domains.{d}")
        mods.append(f"domains.{d}.features")
        mods.append(f"domains.{d}.models")
        mods.append(f"domains.{d}.services")
print("probuster modules:", len(mods))
fails=0
for name in mods:
    try:
        importlib.import_module(name)
    except Exception as e:
        fails+=1
        print("FAIL:", name, "->", type(e).__name__, str(e)[:300])
print("TOTAL FAILS:", fails, "of", len(mods))
