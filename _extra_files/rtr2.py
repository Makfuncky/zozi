import sys, traceback
sys.path.insert(0, '.')
for mod in ['routers.logistics_logistics_status','routers.public_geography_operations','routers.auth','routers.public_effective_permissions_access']:
    try:
        __import__(mod); print("OK", mod)
    except Exception as e:
        print("FAIL", mod, "::", type(e).__name__, str(e).split(chr(10))[0][:100])
        tb=traceback.extract_tb(e.__traceback__)
        for f in tb[-4:]:
            print("   ", f.filename.split('backend')[-1], f.lineno, f.name)
