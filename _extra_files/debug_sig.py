import os, sys, inspect
backend = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend"
sys.path.insert(0, backend); os.chdir(backend)
import importlib.util
spec = importlib.util.spec_from_file_location("controllers.products_controller", os.path.join(backend,"controllers","products_controller.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for fn, obj in inspect.getmembers(m, inspect.isfunction):
    if fn.startswith("_"): continue
    if not fn.lower().startswith(("get","list","create","add","update","edit","delete","remove","cancel","search","set_","save","fetch","retrieve","post")): continue
    try:
        sig = inspect.signature(obj)
    except Exception as e:
        print(fn, "SIG ERR", e); continue
    print(fn, "->", [ (p, str(a), a.__class__.__name__) for p,a in sig.parameters.items() if p not in ("self","cls")])
