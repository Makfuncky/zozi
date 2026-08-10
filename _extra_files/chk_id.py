import sys, importlib, traceback
sys.path.insert(0,'.')
for mod in ['services.identity_admin_service','services.identity_service','routers.admin_identity_operations','routers.public_identity_operations']:
    try:
        m=importlib.import_module(mod)
        n = len(getattr(m,'router',object()).routes) if hasattr(m,'router') else 0
        print("OK ", mod, "(routes=%d)"%n if n else "")
    except Exception as e:
        print("FAIL", mod, "::", type(e).__name__, str(e).split(chr(10))[0][:90])
        for f in traceback.extract_tb(e.__traceback__)[-3:]:
            print("    ", f.filename.split('backend')[-1], f.lineno, f.name)
