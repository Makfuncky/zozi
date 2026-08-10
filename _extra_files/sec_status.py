import os, sys, importlib, traceback, collections
sys.path.insert(0, os.path.abspath('.'))
files = sorted(f for f in os.listdir('routers') if f.endswith('.py') and f!='__init__.py')
sec = [f for f in files if f.startswith(('public_security','public_identity','public_permissions','public_effective','public_supplier_security','admin_identity','admin_treasury_identity','public_audit'))]
print("=== SECURITY-MODULE ROUTER IMPORT STATUS ===")
for f in sec:
    mod='routers.'+f[:-3]
    try:
        importlib.import_module(mod); print("  OK  ", f)
    except Exception as e:
        print("  FAIL", f, "::", type(e).__name__, str(e).split(chr(10))[0][:90])
