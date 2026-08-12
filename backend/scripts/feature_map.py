"""
Complete feature-to-layer audit generator for the ZOZI backend.

Emits backend/FEATURE_LAYER_MAP.md with the schema:

  Sno | Surface | Domain | Feature | utils | jobs | events | dependencies |
  models | db | providers | services | controllers | routers | middlewares |
  connection report

Every file in each architectural layer is classified into a *feature* (domain
module), and connection reports are derived from the real import graph
(controllers->services, services->models, services->providers,
routers->controllers).

Read-only documentation tool. Never deletes or renames anything.
"""

import ast
import os
from collections import defaultdict, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # backend/
BACKEND = ROOT

LAYERS = [
    "models", "db", "providers", "services",
    "controllers", "routers", "middleware", "utils",
    "dependencies", "events", "jobs",
]

# subdir name -> canonical feature key (for layers that use subdirs)
FEATURE_ALIASES = {
    "admin": "admin", "ai": "ai", "analytics": "analytics", "audit": "audit",
    "catalog": "catalog", "commerce": "commerce", "comms": "comms",
    "communication": "comms", "configuration": "configuration", "core": "core",
    "customer": "customer", "delegators": "delegators", "employee": "hr",
    "hr": "hr", "hierarchy": "hr", "finance": "finance", "gateways": "gateway",
    "gateway": "gateway", "geography": "geography", "country": "geography",
    "location_service": "geography", "governance": "governance",
    "identity": "identity", "auth": "identity", "logistics": "logistics",
    "media": "media", "orders": "orders", "permissions": "permissions",
    "products": "products", "security": "security", "supplier": "supplier",
    "suppliers": "supplier", "treasury": "treasury", "uploads": "uploads",
    "promotions": "promotions", "system": "system", "users": "users",
    "common": "common", "mcp": "mcp", "legacy": "legacy",
    "automation": "automation", "image": "image", "voice": "voice",
    "payments": "payments", "generated": "generated",
    "migrations": "migrations",
}

# Display order for feature rows
FEATURE_ORDER = [
    "admin", "analytics", "audit", "catalog", "commerce", "comms", "core",
    "customer", "hr", "finance", "gateway", "geography", "governance",
    "identity", "logistics", "media", "orders", "permissions", "products",
    "security", "supplier", "treasury", "uploads", "promotions", "system",
    "users", "common", "mcp", "legacy", "automation", "image", "voice",
    "payments", "ai", "delegators", "generated", "migrations", "middleware",
    "events", "utils", "dependencies", "jobs", "platform",
]

# Surface = which client/deployment surface the feature primarily serves
SURFACE = {
    "admin": "Admin Web", "analytics": "Admin Web", "audit": "Admin Web",
    "catalog": "Admin + Store", "commerce": "Customer Web + Store",
    "comms": "Cross-channel", "core": "Internal Platform",
    "customer": "Customer Web + Mobile", "hr": "Internal Platform",
    "finance": "Admin + Supplier", "gateway": "System/Integration",
    "geography": "Cross-cutting", "governance": "Admin Web",
    "identity": "Cross-cutting", "logistics": "Supplier + Admin",
    "media": "Cross-cutting", "orders": "Cross-cutting",
    "permissions": "Cross-cutting", "products": "Store + Supplier",
    "security": "Cross-cutting", "supplier": "Supplier Portal",
    "treasury": "Admin + Supplier", "uploads": "Cross-cutting",
    "promotions": "Store", "system": "Internal", "users": "Cross-cutting",
    "common": "Shared", "mcp": "Internal", "legacy": "Cross-cutting",
    "automation": "Internal", "image": "Cross-cutting", "voice": "Cross-cutting",
    "payments": "Cross-cutting", "ai": "Internal", "delegators": "Generated",
    "generated": "Generated", "migrations": "Database", "middleware": "Platform",
    "events": "Platform", "utils": "Platform", "dependencies": "Platform",
    "jobs": "Platform/Async", "platform": "Platform",
}

# Domain = functional grouping
DOMAIN = {
    "admin": "Administration", "analytics": "Analytics", "audit": "Compliance & Audit",
    "catalog": "Catalog", "commerce": "Commerce", "comms": "Communications",
    "core": "People / HR Platform", "customer": "Commerce", "hr": "HR / People",
    "finance": "Finance", "gateway": "Integrations", "geography": "Geography",
    "governance": "Governance", "identity": "Identity & Auth",
    "logistics": "Logistics", "media": "Media", "orders": "Orders",
    "permissions": "Access Control", "products": "Products",
    "security": "Security", "supplier": "Suppliers", "treasury": "Treasury",
    "uploads": "Media / Uploads", "promotions": "Promotions",
    "system": "System", "users": "Identity", "common": "Shared",
    "mcp": "AI / ML", "legacy": "Legacy", "automation": "Automation",
    "image": "Media", "voice": "Communications", "payments": "Payments",
    "ai": "AI / ML", "delegators": "Generated Delegation",
    "generated": "Generated Routers", "migrations": "Database",
    "middleware": "Platform", "events": "Platform", "utils": "Platform",
    "dependencies": "Platform", "jobs": "Async Jobs", "platform": "Platform",
}

# Router filename -> feature classifier (prefix based)
ROUTER_RULES = [
    ("admin_", "admin"), ("core_", "core"), ("store_", "commerce"),
    ("public_commerce_", "commerce"), ("public_comms_", "comms"),
    ("public_finance_", "finance"), ("public_geography_", "geography"),
    ("public_treasury_", "treasury"), ("public_suppliers_", "supplier"),
    ("public_country_", "geography"), ("public_identity_", "identity"),
    ("public_security_", "security"), ("public_effective_", "permissions"),
    ("public_permission", "permissions"), ("public_auth_", "identity"),
    ("public_", "identity"), ("supplier_", "supplier"), ("country_", "geography"),
    ("system_ai_", "ai"), ("ai_", "ai"), ("customer_", "customer"),
    ("finance_", "finance"), ("governance_", "governance"),
    ("logistics_", "logistics"), ("comms_", "comms"),
    ("internal_comms_", "comms"), ("hr_", "hr"), ("product_", "products"),
    ("security_", "security"), ("treasury_", "treasury"),
    ("ws_chat", "comms"), ("mobile_controller", "customer"),
    ("push_notifications", "comms"), ("csp_reporting", "security"),
    ("fraud_", "security"), ("cross_border", "commerce"),
    ("flash_sales", "promotions"), ("parcel_tracking", "logistics"),
    ("shift_handover", "hr"), ("expense_controller", "finance"),
    ("operational_controller", "governance"), ("batch_upload", "uploads"),
    ("upload_jobs", "uploads"), ("payout_approval", "treasury"),
    ("command_center", "admin"), ("frontend_errors", "platform"),
    ("email_controller", "comms"), ("product_moderation", "products"),
    ("product_verification", "products"), ("product_videos", "products"),
]


def py_files(layer_dir):
    out = []
    if not os.path.isdir(layer_dir):
        return out
    for root, dirs, files in os.walk(layer_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for f in files:
            if f.endswith(".py") and f != "__init__.py":
                full = os.path.join(root, f)
                rel = os.path.relpath(full, BACKEND).replace(os.sep, "/")
                out.append((rel, module(rel)))
    return sorted(out)


def module(relpath):
    return relpath[:-3].replace("/", ".")


def feature_for(layer, rel, name):
    parts = rel.split("/")
    if layer in ("models", "db", "providers", "services", "controllers"):
        sub = parts[1] if len(parts) > 1 else ""
        feat = FEATURE_ALIASES.get(sub, sub)
        return feat or layer
    if layer == "routers":
        n = name[:-3] if name.endswith(".py") else name
        for pref, feat in ROUTER_RULES:
            if n.startswith(pref):
                return feat
        return "platform"
    if layer == "middleware":
        return "middleware"
    if layer == "events":
        return "events"
    if layer == "utils":
        # utils are shared; keep under platform except obvious matches
        n = name[:-3] if name.endswith(".py") else name
        for pref, feat in [
            ("auth", "identity"), ("crypto", "security"), ("kms", "security"),
            ("vault", "security"), ("encryption", "security"),
            ("rls", "security"), ("csrf", "security"),
            ("country", "geography"), ("geo", "geography"),
            ("cache", "platform"), ("redis", "platform"),
        ]:
            if n.startswith(pref) or n.endswith(pref):
                return feat
        return "platform"
    if layer == "dependencies":
        return "platform"
    if layer == "jobs":
        sub = parts[1] if len(parts) > 1 else ""
        if sub and sub != name[:-3]:
            return FEATURE_ALIASES.get(sub, sub)
        return "jobs"
    return "platform"


def collect():
    data = defaultdict(lambda: defaultdict(list))  # feature -> layer -> [(rel,mod)]
    for layer in LAYERS:
        for rel, mod in py_files(os.path.join(BACKEND, layer)):
            name = os.path.basename(rel)
            feat = feature_for(layer, rel, name)
            data[feat][layer].append((rel, mod))
    return data


# top-level module roots that map into backend
LAYER_ROOTS = {
    "backend": "backend", "services": "backend.services",
    "models": "backend.models", "controllers": "backend.controllers",
    "providers": "backend.providers", "routers": "backend.routers",
    "utils": "backend.utils", "dependencies": "backend.dependencies",
    "middleware": "backend.middleware", "events": "backend.events",
    "jobs": "backend.jobs", "db": "backend.db", "scripts": "backend.scripts",
}


def normalize(mod):
    """Normalize an imported module name to backend.* form, or None."""
    if not mod:
        return None
    if mod.startswith("backend."):
        return mod
    top = mod.split(".")[0]
    if top in LAYER_ROOTS:
        return LAYER_ROOTS[top] + mod[len(top):]
    return None


def imports_of(rel):
    full = os.path.join(BACKEND, rel)
    try:
        tree = ast.parse(open(full, encoding="utf-8").read())
    except Exception:
        return set()
    found = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            m = normalize(node.module)
            if m:
                found.add(m)
        elif isinstance(node, ast.Import):
            for n in node.names:
                m = normalize(n.name)
                if m:
                    found.add(m)
    return found


def build_connection_report(data):
    report = defaultdict(lambda: {
        "ctrl_to_svc": defaultdict(set),
        "svc_to_model": defaultdict(set),
        "svc_to_provider": defaultdict(set),
        "router_to_ctrl": defaultdict(set),
    })
    mod_index = {}
    for feat, layers in data.items():
        for layer, files in layers.items():
            for rel, mod in files:
                mod_index[mod] = (feat, layer)

    for feat, layers in data.items():
        for rel, mod in layers.get("controllers", []):
            for imp in imports_of(rel):
                if imp.startswith("backend.services"):
                    report[feat]["ctrl_to_svc"][imp].add(rel)
        for rel, mod in layers.get("routers", []):
            for imp in imports_of(rel):
                if imp.startswith("backend.controllers"):
                    report[feat]["router_to_ctrl"][imp].add(rel)
        for rel, mod in layers.get("services", []):
            for imp in imports_of(rel):
                if imp.startswith("backend.models"):
                    report[feat]["svc_to_model"][imp].add(rel)
                elif imp.startswith("backend.providers"):
                    report[feat]["svc_to_provider"][imp].add(rel)
    return report


def bname(rel):
    return os.path.basename(rel)[:-3]


def generate():
    data = collect()
    report = build_connection_report(data)

    lines = []
    lines.append("# ZOZI Backend — Complete Feature-to-Layer Map")
    lines.append("")
    lines.append("> Auto-generated. For every **feature**, lists the files present "
                 "in each architectural layer plus a **connection report** derived "
                 "from the real import graph.")
    lines.append("")
    lines.append("Layers (columns): `utils`, `jobs`, `events`, `dependencies`, "
                 "`models`, `db`, `providers`, `services`, `controllers`, "
                 "`routers`, `middlewares`.")
    lines.append("")
    totals = {l: sum(len(v.get(l, [])) for v in data.values()) for l in LAYERS}
    lines.append("**Totals:** " + " · ".join(
        f"{l}={totals[l]}" for l in LAYERS) +
        f" · features={len([f for f in FEATURE_ORDER if f in data])}")
    lines.append("")

    # Master table
    lines.append("## Master Table")
    lines.append("")
    cols = ["Sno", "Surface", "Domain", "Feature", "utils", "jobs", "events",
            "dependencies", "models", "db", "providers", "services",
            "controllers", "routers", "middlewares"]
    lines.append("| " + " | ".join(cols) + " |")
    lines.append("| " + " | ".join(["---"] * len(cols)) + " |")
    sno = 0
    for feat in FEATURE_ORDER:
        if feat not in data:
            continue
        sno += 1
        layers = data[feat]
        vals = [str(sno), SURFACE.get(feat, "—"), DOMAIN.get(feat, "—"), feat]
        for l in ["utils", "jobs", "events", "dependencies", "models", "db",
                  "providers", "services", "controllers", "routers", "middleware"]:
            cnt = len(layers.get(l, []))
            vals.append(str(cnt) if cnt else "—")
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")

    # Per-feature detail
    lines.append("## Feature Breakdown")
    lines.append("")
    for feat in FEATURE_ORDER:
        if feat not in data:
            continue
        layers = data[feat]
        lines.append(f"### {sno_idx(feat, data)}. {feat}")
        lines.append("")
        lines.append(f"- **Surface:** {SURFACE.get(feat,'—')}  "
                     f"**Domain:** {DOMAIN.get(feat,'—')}")
        lines.append("")
        for layer in LAYERS:
            files = layers.get(layer)
            if not files:
                continue
            lines.append(f"**{layer}** ({len(files)}):")
            lines.append("")
            for rel, mod in files:
                lines.append(f"- `{rel}`")
            lines.append("")
        r = report.get(feat)
        if r:
            lines.append("**Connection report**")
            lines.append("")
            if r["router_to_ctrl"]:
                lines.append("Routers → Controllers:")
                for ctrl, routers in sorted(r["router_to_ctrl"].items()):
                    rl = ", ".join(bname(x) for x in sorted(routers))
                    lines.append(f"- `{ctrl}` ← {rl}")
                lines.append("")
            if r["ctrl_to_svc"]:
                lines.append("Controllers → Services:")
                for svc, ctrls in sorted(r["ctrl_to_svc"].items()):
                    cl = ", ".join(bname(x) for x in sorted(ctrls))
                    lines.append(f"- `{svc}` ← {cl}")
                lines.append("")
            if r["svc_to_model"]:
                lines.append("Services → Models:")
                for mdl, svcs in sorted(r["svc_to_model"].items()):
                    sl = ", ".join(bname(x) for x in sorted(svcs))
                    lines.append(f"- `{mdl}` ← {sl}")
                lines.append("")
            if r["svc_to_provider"]:
                lines.append("Services → Providers:")
                for prv, svcs in sorted(r["svc_to_provider"].items()):
                    sl = ", ".join(bname(x) for x in sorted(svcs))
                    lines.append(f"- `{prv}` ← {sl}")
                lines.append("")
        lines.append("")
    return "\n".join(lines)


def sno_idx(feat, data):
    # recompute sno consistently with the table order
    i = 0
    for f in FEATURE_ORDER:
        if f in data:
            i += 1
            if f == feat:
                return i
    return i


def main():
    out = generate()
    dest = os.path.join(ROOT, "FEATURE_LAYER_MAP.md")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(out)
    print(f"Wrote {dest} ({len(out)} bytes)")


if __name__ == "__main__":
    main()
