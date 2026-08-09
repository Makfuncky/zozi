import os, marshal, types, sys
cache = "scripts/system_trackers/__pycache__"
def load(name):
    with open(os.path.join(cache, name+".cpython-310.pyc"),"rb") as f:
        f.read(16); code = marshal.load(f)
    mod = types.ModuleType(name); mod.__file__ = name+".py"
    sys.modules[name] = mod
    exec(code, mod.__dict__); return mod
for h in ["database_audit","design_audit","health_audit"]:
    try: load(h); print("loaded helper", h)
    except Exception as e: print("helper",h,"err",e)
with open(os.path.join(cache,"system_architecture_audit.cpython-310.pyc"),"rb") as f:
    f.read(16); maincode = marshal.load(f)
mainmod = types.ModuleType("__main__"); mainmod.__name__="__main__"
mainmod.__file__ = "scripts/system_trackers/system_architecture_audit.py"
sys.argv = ["system_architecture_audit.py"]
sys.path.insert(0, "scripts/system_trackers")
exec(maincode, mainmod.__dict__)
