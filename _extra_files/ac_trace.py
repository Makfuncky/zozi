import sys, traceback
sys.path.insert(0, '.')
try:
    import controllers.auth_controller as m
    print("auth_controller OK")
except Exception as e:
    print("auth_controller FAIL:", type(e).__name__, str(e).split(chr(10))[0][:120])
    for f in traceback.extract_tb(e.__traceback__):
        print("   ", f.filename.split('backend')[-1], f.lineno, f.name, '|', (f.line or '').strip()[:70])
