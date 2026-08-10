import importlib, pathlib, sys, traceback

BACKEND = pathlib.Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend")
sys.path.insert(0, str(BACKEND))
layers = [BACKEND / "routers", BACKEND / "middleware", BACKEND / "controllers"]

ok = 0
bad = 0
for d in layers:
    for p in sorted(d.rglob("*.py")):
        rel = p.relative_to(BACKEND)
        mod = ".".join(rel.with_suffix("").parts)
        try:
            importlib.import_module(mod)
            ok += 1
        except Exception as e:
            bad += 1
            # ignore DB/table/env errors; flag only import/syntax/attribute errors
            etype = type(e).__name__
            msg = str(e).splitlines()[0][:160]
            print(f"  IMPORT FAIL [{etype}] {rel}: {msg}")

print(f"\nLayer modules imported OK: {ok}; failed: {bad}")
