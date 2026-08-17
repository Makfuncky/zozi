import ast, pathlib

TARGETS = {
    "create_shipment": "services/logistics/logistics_logistics_status_service.py",
    "scan_lookup_shipment": "services/logistics/logistics_logistics_status_service.py",
    "get_active_shipments": "services/logistics/logistics_logistics_status_service.py",
    "get_shipment_history": "services/logistics/logistics_logistics_status_service.py",
    "get_shipment_events": "services/logistics/logistics_logistics_status_service.py",
    "scan_shipment_event": "services/logistics/logistics_logistics_status_service.py",
    "update_shipment_status": "services/logistics/logistics_logistics_status_service.py",
    "get_distribution_channels": "services/logistics/logistics_logistics_status_service.py",
    "update_shipment_event_gps": "services/logistics/logistics_logistics_status_service.py",
    "upload_my_cod_remittance_receipt": "services/logistics/logistics_partner_verify_service.py",
    "upload_lp_document": "services/logistics/logistics_partner_verify_service.py",
}

def top_level_symbols(modpath):
    src = pathlib.Path(modpath).read_text(encoding="utf-8", errors="replace")
    tree = ast.parse(src)
    syms = {}
    for n in tree.body:
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            syms[n.name] = ("def", getattr(n, "lineno", None))
        elif isinstance(n, ast.Assign):
            for t in n.targets:
                if isinstance(t, ast.Name):
                    syms[t.id] = ("assign", getattr(n, "lineno", None))
        elif isinstance(n, ast.ImportFrom):
            for a in n.names:
                syms[a.asname or a.name] = ("imp:" + n.module, getattr(n, "lineno", None))
    return syms

svc_root = pathlib.Path("services")
results = {}
for name, target in TARGETS.items():
    target_path = pathlib.Path(target)
    candidates = []
    for p in svc_root.rglob("*.py"):
        if p == target_path:
            continue
        if "test" in p.parts or p.name.startswith("__"):
            continue
        syms = top_level_symbols(p)
        if name in syms:
            candidates.append((str(p), syms[name]))
    results[name] = candidates

for name in TARGETS:
    print("===", name, "===")
    for c in results[name]:
        print("   ", c[0], c[1])
