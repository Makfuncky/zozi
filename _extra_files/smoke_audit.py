import importlib, os, sys
sys.path.insert(0, os.getcwd())
try:
    mod = importlib.import_module("routers.public_comms_communication_audit")
    r = getattr(mod, "router", None)
    paths = [(sorted(getattr(route, "methods", [])), route.path) for route in r.routes] if r else []
    print("generated audit router OK; routes:", paths)
except Exception as e:
    print("IMPORT ERROR:", repr(e))
try:
    importlib.import_module("routers.audit")
    print("WARN: routers.audit still importable")
except ModuleNotFoundError:
    print("routers.audit correctly removed")
