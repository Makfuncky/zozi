"""ZOZI feature-domain + module-layered audit (v2).

Canonical feature domains = subpackages under controllers / services / models.
Routers are flat and encoded; we map each router module to a feature by the
domain subpackage it imports (controllers.X / services.X).

Outputs JSON to backend/.audit/feature_audit2.json
"""
from __future__ import annotations
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import coherence_gate as g

BACKEND = g.BACKEND
OUT = os.path.join(BACKEND, ".audit")
os.makedirs(OUT, exist_ok=True)

layers, allmods, graph, mc = g.build()

DOMAIN = ["controllers", "services", "models"]
INFRA = {"db","utils","middleware","providers","events","jobs","dependencies","scripts","schemas","tests","routers","other"}

# Canonical feature names (subpackages + flat model features). A module is
# attributed to a feature by its OWN basename first (e.g. services/security/
# fraud_service.py -> "fraud"), then by its enclosing subpackage. This avoids
# the false "orphan" bug where fraud/commission/permissions services in another
# package's directory were not counted under their own feature.
FEATURES = {
    "admin","ai","ai_upload","analytics","audit","catalog","commerce","commission",
    "common","comms","communication","core","countries","country","country_control",
    "country_enhancements","customer","delegators","employee","employee_models","erp",
    "extracted","finance","fraud","gateways","geography","governance","hierarchy","hr",
    "identity","incident","location_service","logistics","marketing","mcp","media_models",
    "mixins","onboarding","orders","payments","permissions","products","promotions",
    "security","supplier","suppliers","system","treasury","upload_job","user","users",
}

def subpkg(m):
    p = m.split(".")
    if len(p) > 1 and p[0] in DOMAIN:
        return p[1]
    return None

def feat_of(m):
    """Best-effort feature attribution: basename keyword wins, else subpackage."""
    base = m.split(".")[-1]
    for f in FEATURES:
        if base == f or base.startswith(f + "_"):
            return f
    return subpkg(m)

# canonical features = subpackages in domain layers
feat_modules = collections.defaultdict(lambda: collections.defaultdict(list))
for m in allmods:
    sp = feat_of(m)
    if sp:
        feat_modules[sp][m.split(".")[0]].append(m)

# map routers -> feature via imported domain subpackages
router_feat = {}
router_unmapped = []
for m in layers.get("routers", []):
    cand = collections.Counter()
    for t in graph.get(m, ()):
        sp = feat_of(t)
        if sp and sp != "extracted":
            cand[sp] += 1
    if cand:
        router_feat[m] = cand.most_common(1)[0][0]
    else:
        router_unmapped.append(m)
        router_feat[m] = None

# feature -> routers count
feat_routers = collections.Counter()
for m, f in router_feat.items():
    if f:
        feat_routers[f] += 1

# ---- feature -> feature dependency edges (domain subpackage level) ----
feat_edges = collections.defaultdict(set)
feat_edge_kind = collections.Counter()  # (src,dst) -> count
for m, dsts in graph.items():
    sp = feat_of(m)
    if not sp:
        continue
    for t in dsts:
        tsp = feat_of(t)
        if tsp and tsp != sp:
            feat_edges[sp].add(tsp)
            feat_edge_kind[(sp, tsp)] += 1

# ---- presence completeness ----
all_feats = sorted(feat_modules.keys())
print("=== FEATURE INVENTORY (controllers/services/models subpackages) ===")
print(f"{'feature':16s} {'ctrl':>5s} {'svc':>5s} {'model':>5s} {'rtr':>5s}")
gap_rows = []
for f in all_feats:
    ctrl = len(feat_modules[f].get("controllers", []))
    svc = len(feat_modules[f].get("services", []))
    model = len(feat_modules[f].get("models", []))
    rtr = feat_routers.get(f, 0)
    print(f"{f:16s} {ctrl:5d} {svc:5d} {model:5d} {rtr:5d}")

# ---- gaps ----
print("\n=== GAP ANALYSIS ===")
# service feature without model (capability not persisted)
svc_no_model = [f for f in all_feats if feat_modules[f].get("services") and not feat_modules[f].get("models")]
print("\n[SVC without MODEL] (service layer exists, no model of same feature):")
for f in svc_no_model:
    print("  -", f)
# controller feature without service
ctrl_no_svc = [f for f in all_feats if feat_modules[f].get("controllers") and not feat_modules[f].get("services")]
print("\n[CTRL without SVC]:")
for f in ctrl_no_svc:
    print("  -", f)
# model without service/controller (genuine orphan model feature)
model_no_svc = [f for f in all_feats if feat_modules[f].get("models") and not feat_modules[f].get("services") and not feat_modules[f].get("controllers")]
print("\n[MODEL without SVC/CTRL] (genuine orphan model features):")
for f in model_no_svc:
    print("  -", f)
# model + service but no controller (HTTP surface gap)
model_svc_no_ctrl = [f for f in all_feats if feat_modules[f].get("models") and feat_modules[f].get("services") and not feat_modules[f].get("controllers")]
print("\n[MODEL+SVC without CTRL] (backed but no HTTP controller):")
for f in model_svc_no_ctrl:
    print("  -", f)

# ---- feature coupling (top downstream dependencies) ----
print("\n=== TOP FEATURE COUPLING (out-degree: features this feature imports) ===")
deg = {f: len(feat_edges[f]) for f in all_feats}
for f in sorted(deg, key=lambda x: -deg[x])[:25]:
    print(f"  {f:16s} -> {deg[f]:3d}  {sorted(feat_edges[f])}")

# routers mapped stats
print("\n=== ROUTER MAPPING ===")
print("routers total:", len(router_feat))
print("mapped to a feature:", sum(1 for v in router_feat.values() if v))
print("unmapped (no domain import):", len(router_unmapped))
for m in router_unmapped[:40]:
    print("   unmapped:", m)

data = {
    "feature_inventory": {f: {"controllers": len(feat_modules[f].get("controllers",[])),
                               "services": len(feat_modules[f].get("services",[])),
                               "models": len(feat_modules[f].get("models",[])),
                               "routers": feat_routers.get(f,0)} for f in all_feats},
    "svc_no_model": svc_no_model,
    "ctrl_no_svc": ctrl_no_svc,
    "model_no_svc": model_no_svc,
    "model_svc_no_ctrl": model_svc_no_ctrl,
    "feat_edges": {k: sorted(v) for k,v in feat_edges.items()},
    "feat_out_degree": deg,
    "router_unmapped": router_unmapped,
}
with open(os.path.join(OUT, "feature_audit2.json"), "w") as fp:
    json.dump(data, fp, indent=2)
print("\nwrote", os.path.join(OUT, "feature_audit2.json"))
