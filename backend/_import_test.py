import importlib, pkgutil, sys, os, traceback
import structlog
logger = structlog.get_logger(__name__)

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-import-diagnostic-only-1234567890")
os.environ.setdefault("FIELD_ENCRYPTION_KEY", "test-enc-key-1234567890abcdef1234567890abcdef")

SERVICE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SERVICE_DIR)

PKG_ROOTS = ["controllers", "services", "routers", "events", "providers", "utils", "models", "dependencies", "middleware"]

def iter_modules(pkgname, pkgpath):
    mods = []
    for info in pkgutil.walk_packages([pkgpath], prefix=pkgname + "."):
        mods.append(info.name)
    mods.sort()
    return mods

all_mods = []
for pkg in PKG_ROOTS:
    p = os.path.join(SERVICE_DIR, pkg)
    if os.path.isdir(p):
        all_mods.extend(iter_modules(pkg, p))

# also top-level backend modules
for fn in sorted(os.listdir(SERVICE_DIR)):
    if fn.endswith(".py") and fn not in ("main.py", "run_server.py", "_import_test.py") and not fn.startswith(("_", ".")):
        all_mods.append(fn[:-3])

results = {"OK": [], "OK_NO_ROUTER": [], "FAILED": []}
for m in all_mods:
    try:
        importlib.import_module(m)
        if "routers" in m:
            results["OK"].append(m)
        else:
            results["OK_NO_ROUTER"].append(m)
    except (ValueError, TypeError, KeyError, IndexError, AttributeError, RuntimeError, OSError, IOError, EOFError, ImportError, NameError, StopIteration, ArithmeticError, AssertionError, UnicodeError, NotImplementedError, RecursionError, ReferenceError, SystemError, BufferError, LookupError) as e:
        logger.exception("unhandled exception", error=str(e))
        results["FAILED"].append((m, type(e).__name__, str(e).splitlines()[-1] if str(e) else repr(e)))

print(f"TOTAL={len(all_mods)} OK={len(results['OK'])+len(results['OK_NO_ROUTER'])} FAILED={len(results['FAILED'])}")
print("=== FAILED ===")
for m, t, msg in sorted(results["FAILED"]):
    print(f"{m} :: {t} :: {msg[:160]}")
