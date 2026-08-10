import sys, importlib
sys.path.insert(0,'.')
try:
    import routers.public_security_registration as m
    print("OK import")
    print("  imports models?:", "from models" in open("routers/public_security_registration.py",encoding="utf-8").read())
    print("  imports middleware.csrf?:", "middleware.csrf_middleware" in open("routers/public_security_registration.py",encoding="utf-8").read())
    print("  routes:", [r.path for r in m.router.routes])
except Exception as e:
    import traceback; traceback.print_exc()
