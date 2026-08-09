import pathlib, sys, re
sys.path.insert(0, "scripts/system_trackers")
import system_architecture_audit as A

stop = set(A.PLACEMENT_STOP_TOKENS)
aliases = A.PLACEMENT_ALIAS_TO_DOMAIN
surfaces = {str(x).lower() for x in A.DEFAULT_SURFACE_NAMES}
print("is 'management' stop?", "management" in stop)
print("is 'fulfillment' stop?", "fulfillment" in stop)
print("is 'tracking' stop?", "tracking" in stop)
print("is 'browsing' stop?", "browsing" in stop)
print("is 'service' stop?", "service" in stop)
print("is 'api' stop?", "api" in stop)
print("is 'controller' stop?", "controller" in stop)


def _tokens(s):
    return [t.lower() for t in re.split(r"[^A-Za-z0-9]+", s) if t]


def _surface(t):
    for x in t:
        if x in surfaces:
            return x
    return None


def _domain(t):
    for x in t:
        if aliases.get(x):
            return aliases.get(x)
    return None


def _has_op(t, s, d):
    for x in t:
        if len(x) < 3:
            continue
        if x in stop:
            continue
        if s and x == s:
            continue
        if d and (x == d or aliases.get(x) == d):
            continue
        return True
    return False


cands = ["tracking", "fulfillment", "browsing", "creation", "listing", "config", "sync",
         "ingest", "export", "import", "search", "upload", "download", "notify", "report",
         "manage", "handle", "process", "resolve", "verify", "approve", "review", "publish",
         "scan", "merge", "compute", "analyze", "monitor", "register", "activate"]
stem = "admin_orders"
toks = _tokens(stem)
s = _surface(toks)
d = _domain(toks)
print("\nFor stem", stem, "surf", s, "dom", d)
ok = [c for c in cands if _has_op(_tokens(stem + "_" + c), s, d)]
print("operation words that make has_op=True:", ok)
print("candidates that are stopwords:", [c for c in cands if c in stop])
