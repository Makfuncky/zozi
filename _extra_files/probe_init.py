import importlib, traceback

mods = [
    'controllers.identity.iam_controller',
    'controllers.logistics.logistics_health_list_controller',
    'models.supplier.suppliers',
]
for m in mods:
    try:
        importlib.import_module(m)
        print(f"OK   {m}")
    except Exception as e:
        print(f"FAIL {m}: {type(e).__name__}: {e}")
