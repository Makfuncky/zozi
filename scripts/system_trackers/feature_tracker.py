#!/usr/bin/env python3
"""
ZOZI Feature Tracker v2 — Description-Driven Auto-Discovery
============================================================
Reads feature_definitions.yaml (descriptions only), DISCOVERS all relevant
files across backend/web/mobile/shared/tests, verifies capabilities with
evidence, detects duplicate/dead/extra files, diffs against last run, and
regenerates the 6-section CODEBASE_STATUS_MATRIX.

Engines: seed+IDF lexical scoring · symbol/route match · import-graph
expansion · capability evidence · duplicate/dead detector · state diff ·
optional Ollama semantic blend.

Usage:
    pip install pyyaml
    python scripts/feature_tracker.py                     # structural
    python scripts/feature_tracker.py --with-ollama       # + AI blend
    python scripts/feature_tracker.py --threshold 0.30 --output out.md
"""
from __future__ import annotations
import argparse, json, math, re, sys, time
from collections import defaultdict
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ pip install pyyaml"); sys.exit(1)

ROOT       = Path(__file__).resolve().parent.parent
DEF_FILE   = ROOT / "scripts" / "feature_definitions.yaml"
STATE_FILE = ROOT / "scripts" / "tracker_state.json"
DEFAULT_OUT= ROOT / "documents" / "CODEBASE_STATUS_MATRIX_AUTO.md"

EXCLUDE = {"node_modules",".next",".git","__pycache__","versions_archive",
           ".venv","venv","dist","build","coverage",".expo","artifacts"}
EXTS = {".py",".ts",".tsx"}
MAX_CHARS = 500_000

STOP = set("""the and for with this that from into over under each every all
any some when then than while where which who because between through during
before after again further once here there why how not only own same such too
very just also both but nor about against most more less least few much many
can will did does has have had are was were been being its they them their
you your our his her him she you'll it's don't won't via per etc able must
should could would may might need needs used using use one two three new
""".split())

CAMEL_RE   = re.compile(r"[A-Z][a-z]+")
BACKTICK_RE= re.compile(r"`([^`\n]+)`")
PASCAL_RE  = re.compile(r"\b([A-Z][a-z]+(?:[A-Z][a-z]+)+)\b")
SNAKE_RE   = re.compile(r"\b([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\b")
ROUTE_RE   = re.compile(r"@router\.(?:get|post|put|patch|delete|websocket)\(\s*[\"']([^\"']+)")
PY_IMP_RE  = re.compile(r"^\s*(?:from|import)\s+([a-zA-Z_][\w\.]*)", re.M)
TS_IMP_RE  = re.compile(r"from\s+[\"']([^\"']+)[\"']|import\s*\(\s*[\"']([^\"']+)[\"']")

def split_camel(s): return [m.lower() for m in CAMEL_RE.findall(s)]

def tokenize_name(name: str) -> set:
    toks = set()
    for p in re.split(r"[^A-Za-z0-9]+", name):
        if not p: continue
        toks.add(p.lower()); toks.update(split_camel(p))
    return {t for t in toks if len(t) >= 3 or t in {"ai","db","ws","qr","ui","dlp"}} - STOP

# ============================================================================
# REPO SCANNER
# ============================================================================
class Repo:
    def __init__(self, root: Path):
        self.root = root; self.files = {}; self._scan()

    def _scan(self):
        for p in self.root.rglob("*"):
            if not p.is_file() or p.suffix not in EXTS: continue
            if any(ex in p.parts for ex in EXCLUDE): continue
            if p.stat().st_size > MAX_CHARS: continue
            try: text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception: continue
            rel = str(p.relative_to(self.root)).replace("\\", "/")
            self.files[rel] = {
                "text": text, "low": text.lower(),
                "name_tokens": tokenize_name(p.stem),
                "path_tokens": tokenize_name(rel),
            }
        print(f"📁 Scanned {len(self.files)} source files")

def classify(rel: str) -> str:
    r = rel.lower()
    if r.startswith("backend/routers/"):            return "backend_router"
    if r.startswith("backend/controllers/"):        return "backend_controller"
    if r.startswith("backend/services/"):           return "backend_service"
    if r.startswith("backend/models/") or (r.startswith("backend/") and "/models/" in r): return "backend_model"
    if "alembic/versions" in r:                     return "migration"
    if r.startswith("backend/tests/") or r.startswith("backend/scripts/test"): return "test_backend"
    if "/__tests__/" in r and "mobile_app" in r:    return "test_mobile"
    if "/__tests__/" in r:                          return "test_web"
    if "/e2e/" in r:                                return "e2e"
    if r.startswith("frontend/web_app/src/app/") and r.endswith("page.tsx"): return "web_page"
    if r.startswith("frontend/web_app/src/components/"): return "web_component"
    if r.startswith("frontend/web_app/src/lib/"):   return "web_lib"
    if r.startswith("frontend/mobile_app/app/") and r.endswith(".tsx"): return "mobile_screen"
    if r.startswith("frontend/shared/"):            return "shared"
    return "other"

def build_graph(repo: Repo):
    stems = {}
    for rel in repo.files: stems.setdefault(Path(rel).stem, rel)
    edges = defaultdict(set)
    for rel, f in repo.files.items():
        if rel.endswith(".py"):
            mods = [m.group(1).split(".")[-1] for m in PY_IMP_RE.finditer(f["text"])]
        else:
            mods = [(m.group(1) or m.group(2) or "").split("/")[-1] for m in TS_IMP_RE.finditer(f["text"])]
        for mod in mods:
            if mod in stems and stems[mod] != rel: edges[rel].add(stems[mod])
    return edges

def route_duplicates(repo: Repo):
    routes = {rel: set(ROUTE_RE.findall(f["text"])) for rel, f in repo.files.items()
              if classify(rel) == "backend_router"}
    dups, items = [], list(routes.items())
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            shared = items[i][1] & items[j][1]
            if shared: dups.append((items[i][0], items[j][0], sorted(shared)[:3]))
    return dups

def dead_candidates(repo: Repo):
    main_low = repo.files.get("backend/main.py", {}).get("low", "")
    dead = []
    for rel, f in repo.files.items():
        c, stem = classify(rel), Path(rel).stem
        if c == "backend_router":
            if stem not in main_low: dead.append((rel, "router not registered in main.py"))
        elif c in ("backend_service", "backend_controller"):
            if not any(stem in o["low"] for or_, o in repo.files.items()
                       if or_ != rel and or_.endswith(".py") and or_ not in rel):
                dead.append((rel, "never imported by any module"))
    return dead

# ============================================================================
# FEATURE ANALYSIS
# ============================================================================
def extract_seeds(feat: dict) -> dict:
    raw = list(feat.get("keywords") or [])
    desc = feat.get("description", "") or ""
    raw += BACKTICK_RE.findall(desc) + PASCAL_RE.findall(desc) + SNAKE_RE.findall(desc)
    raw += re.findall(r'"([^"\n]{3,40})"', desc)
    seeds = defaultdict(float)
    for chunk in raw:
        for tok in tokenize_name(chunk): seeds[tok] += 1.0
    return dict(seeds)

def extract_caps(desc: str):
    caps = []
    for line in desc.splitlines():
        t = line.strip()
        if not t or len(t) > 220: continue
        if t.startswith(("- ", "* ", "• ")) or re.match(r"^\d+\.", t) or "**" in t:
            phrase = re.sub(r"[`*|]", "", t).strip(" -•")
            toks = [x for x in tokenize_name(phrase) if len(x) >= 4]
            if 4 <= len(phrase) <= 200 and len(toks) >= 2:
                caps.append({"phrase": phrase[:140], "tokens": toks})
    return caps[:40]

def find_line(f: dict, tok: str) -> int:
    idx = f["low"].find(tok)
    return f["text"].count("\n", 0, idx) + 1 if idx >= 0 else 0

class Analyzer:
    def __init__(self, repo: Repo, threshold: float):
        self.repo, self.th = repo, threshold
        self.df = defaultdict(int)
        self.graph = build_graph(repo)
        self.dups = route_duplicates(repo)
        self.dead = dead_candidates(repo)

    def _weights(self, seeds: dict):
        for tok in seeds:
            if self.df[tok] == 0:
                self.df[tok] = sum(1 for f in self.repo.files.values() if tok in f["low"])
        return {t: s * (1.0 / (1 + math.log(1 + self.df[t]))) for t, s in seeds.items()}

    def analyze(self, feat: dict):
        w = self._weights(extract_seeds(feat))
        base = {}
        for rel, f in self.repo.files.items():
            if not any(t in f["low"] for t in w): continue
            s = 0.0
            for t, wt in w.items():
                if t in f["name_tokens"]: s += 2.2 * wt
                elif t in f["path_tokens"]: s += 1.1 * wt
                c = f["low"].count(t)
                if c: s += min(c, 6) * 0.30 * wt
            base[rel] = s / (s + 8.0)
        members = {r: sc for r, sc in base.items() if sc >= self.th}
        # graph expansion
        for m, ms in list(members.items()):
            for n in self.graph.get(m, ()): 
                boosted = base.get(n, 0.0) + 0.12 * ms
                if n not in members and boosted >= self.th * 0.8:
                    members[n] = boosted
        # route-link expansion (frontend mentions backend route)
        for rel, f in list(self.repo.files.items()):
            if classify(rel) in ("web_page", "web_component", "web_lib", "mobile_screen"):
                for rrel in [r for r in members if classify(r) == "backend_router"]:
                    if any(rt in f["low"] for rt in ROUTE_RE.findall(self.repo.files[rrel]["text"]) if len(rt) > 6):
                        members.setdefault(rel, max(members.get(rel, 0), self.th * 0.85)); break
        return self._report(feat, members, base)

    def _report(self, feat, members, base):
        layers = {classify(m) for m in members}
        has = lambda *ls: any(l in layers for l in ls)
        backend_score = sum([has("backend_router"), has("backend_controller", "backend_service"),
                             has("backend_model", "migration")]) / 3.0
        frontend_score = sum([has("web_page", "web_component"), has("mobile_screen")]) / 2.0
        test_score = 1.0 if has("test_backend", "test_web", "test_mobile", "e2e") else 0.0
        # capabilities
        caps, found = extract_caps(feat.get("description", "")), 0
        for cap in caps:
            best, ev = 0, None
            for m in members:
                f = self.repo.files[m]
                hit = [t for t in cap["tokens"] if t in f["low"]]
                if len(hit) > best and len(hit) >= max(2, len(cap["tokens"]) // 2):
                    best, ev = len(hit), (m, find_line(f, hit[0]))
            cap["evidence"] = ev
            if ev: found += 1
        cap_score = (found / len(caps)) if caps else 0.5
        pct = 100 * (0.35 * backend_score + 0.30 * frontend_score +
                     0.15 * test_score + 0.20 * cap_score)
        # must_have cap
        missing_mh = [m for m in (feat.get("must_have") or []) if m not in self.repo.files]
        if missing_mh: pct = min(pct, 60.0)
        feat_dups = [d for d in self.dups if d[0] in members or d[1] in members]
        feat_dead = [d for d in self.dead if d[0] in members]
        return {
            "id": feat["id"], "name": feat["name"], "scope": feat.get("scope", ""),
            "section": feat.get("matrix_section", ""), "weight": feat.get("weight", 5),
            "members": members, "layers": sorted(layers), "caps": caps,
            "cap_found": found, "pct": round(pct, 1), "missing_must_have": missing_mh,
            "dups": feat_dups, "dead": feat_dead,
            "scores": {"backend": backend_score, "frontend": frontend_score,
                       "tests": test_score, "caps": cap_score},
        }

# ============================================================================
# OLLAMA (OPTIONAL)
# ============================================================================
class Ollama:
    def __init__(self, model="llama3.1", url="http://localhost:11434"):
        self.model, self.url, self.ok = model, url, self._ping()
    def _ping(self):
        try:
            import urllib.request
            with urllib.request.urlopen(f"{self.url}/api/tags", timeout=2) as r: return r.status == 200
        except Exception: return False
    def verify(self, feat_name, desc, top_files):
        if not self.ok: return None
        import urllib.request
        prompt = (f"Feature: {feat_name}\nSpec:\n{desc[:1500]}\nDiscovered files:\n"
                  + "\n".join(top_files[:10]) +
                  "\nReply JSON only: {\"confidence\":0.0-1.0,\"missing\":\"...\"}")
        try:
            req = urllib.request.Request(f"{self.url}/api/generate",
                data=json.dumps({"model": self.model, "prompt": prompt, "stream": False,
                                 "format": "json", "options": {"temperature": 0.2}}).encode(),
                headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=90) as r:
                d = json.loads(json.loads(r.read().decode())["response"])
                return float(d.get("confidence", 0.5)), d.get("missing", "")
        except Exception as e:
            return None

# ============================================================================
# REPORT GENERATION
# ============================================================================
def esc(s): return str(s).replace("|", "/")

def generate(results, prev_state, out: Path, ai_notes):
    L = ["# ZOZI Codebase Status Matrix — AUTO-DISCOVERED (v2)", "",
         f"**Generated:** {time.strftime('%Y-%m-%d %H:%M:%S')} · **Engine:** description-driven auto-discovery",
         "", "## 📊 Executive Summary", "", "| Section | Features | Weighted % |", "|---|---|---|"]
    secs = defaultdict(lambda: [0, 0.0])
    for r in results:
        secs["🗂️ Overview"][0] += 1; secs["🗂️ Overview"][1] += r["pct"] * r["weight"]
        for s in ["§I","§II","§III","§IV","§V"]:
            if s in r["section"]: secs[s][0] += 1; secs[s][1] += r["pct"] * r["weight"]
    names = {"🗂️ Overview":"🗂️ Systems Overview","§I":"🌐 I Infrastructure","§II":"👤 II Customer",
             "§III":"🏭 III Supplier","§IV":"🚚 IV Logistor","§V":"👨‍💼 V Admin"}
    for k, (n, wsum) in secs.items():
        p = wsum / n if n else 0
        L.append(f"| {names.get(k,k)} | {n} | **{p:.1f}%** |")
    L += ["", "---", "", "## 🗂️ Systems Overview — Master Quick Reference", "",
          "| # | System | Scope | Files | Caps | Dup/Dead | Status | % |", "|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(results, 1):
        em = "✅" if r["pct"] >= 90 else "⚠️" if r["pct"] >= 40 else "❌"
        L.append(f"| {i} | {em} **{esc(r['name'])}** | {esc(r['scope'])} | {len(r['members'])} | "
                 f"{r['cap_found']}/{len(r['caps'])} | {len(r['dups'])}/{len(r['dead'])} | {em} | **{r['pct']}%** |")
    # section tables
    for s, title in [("§I","🌐 Section I — System & Infrastructure"),("§II","👤 Section II — Customer"),
                     ("§III","🏭 Section III — Supplier"),("§IV","🚚 Section IV — Logistor"),
                     ("§V","👨‍💼 Section V — Admin")]:
        rows = [r for r in results if s in r["section"]]
        if not rows: continue
        L += ["", "---", f"## {title}", "",
              "| Feature | Backend | Web | Mobile | Tests | Caps | % |", "|---|---|---|---|---|---|---|"]
        for r in rows:
            ly = r["layers"]
            L.append(f"| {esc(r['name'])} | {'✅' if any(l.startswith('backend') for l in ly) else '❌'} | "
                     f"{'✅' if any(l in ('web_page','web_component') for l in ly) else '❌'} | "
                     f"{'✅' if 'mobile_screen' in ly else '❌'} | "
                     f"{'✅' if any(l.startswith('test') or l=='e2e' for l in ly) else '❌'} | "
                     f"{r['cap_found']}/{len(r['caps'])} | **{r['pct']}%** |")
    # appendix: findings
    L += ["", "---", "## 🔎 Appendix — Per-Feature Discovery & Findings", ""]
    new_state = {}
    for r in results:
        prev_files = set(prev_state.get(r["id"], {}).get("files", []))
        new_files = sorted(set(r["members"]) - prev_files)
        new_state[r["id"]] = {"files": sorted(r["members"]), "pct": r["pct"]}
        L += [f"### {r['id']} — {r['name']}  ({r['pct']}%)", ""]
        by_layer = defaultdict(list)
        for m in sorted(r["members"]): by_layer[classify(m)].append(m)
        for layer in ["backend_router","backend_controller","backend_service","backend_model",
                      "web_page","web_component","mobile_screen","shared","test_backend","test_web","test_mobile","e2e"]:
            if by_layer.get(layer):
                tag = " (NEW)" if False else ""
                files = ", ".join(f"`{f}`{' 🆕' if f in new_files else ''}" for f in by_layer[layer][:10])
                L.append(f"- **{layer}**: {files}")
        L.append("")
        if r["caps"]:
            L.append("**Capability checklist:**")
            for c in r["caps"]:
                if c["evidence"]: L.append(f"- ✅ {esc(c['phrase'])} — `{c['evidence'][0]}:{c['evidence'][1]}`")
                else:             L.append(f"- ❌ {esc(c['phrase'])} — no evidence found")
            L.append("")
        findings = []
        if r["missing_must_have"]: findings.append("must_have missing: " + ", ".join(r["missing_must_have"]))
        for a, b, sh in r["dups"]: findings.append(f"DUPLICATE routes {a} ↔ {b} ({', '.join(sh)})")
        for d, why in r["dead"]: findings.append(f"DEAD/UNWIRED: {d} ({why})")
        if new_files: findings.append(f"NEW since last run ({len(new_files)}): " + ", ".join(new_files[:8]))
        if ai_notes.get(r["id"]): findings.append("AI: " + ai_notes[r["id"]])
        if findings:
            L.append("**Findings:**")
            L += [f"- ⚠️ {f}" for f in findings]
        L.append("")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    STATE_FILE.write_text(json.dumps(new_state, indent=1), encoding="utf-8")
    return out

# ============================================================================
# MAIN
# ============================================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-ollama", action="store_true")
    ap.add_argument("--threshold", type=float, default=0.32)
    ap.add_argument("--output", default=str(DEFAULT_OUT))
    args = ap.parse_args()

    print("=" * 70); print("  ZOZI FEATURE TRACKER v2 — AUTO-DISCOVERY"); print("=" * 70)
    repo = Repo(ROOT)
    defs = yaml.safe_load(DEF_FILE.read_text(encoding="utf-8"))
    feats = defs.get("features", [])
    prev = json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {}
    an = Analyzer(repo, args.threshold)
    oll = Ollama() if args.with_ollama else None
    results, ai_notes = [], {}
    for i, f in enumerate(feats, 1):
        print(f"  [{i}/{len(feats)}] {f['id']}: {f['name'][:60]}...", end="")
        r = an.analyze(f)
        if oll and oll.ok:
            top = sorted(r["members"], key=lambda m: -r["members"][m])[:8]
            v = oll.verify(f["name"], f.get("description", ""), top)
            if v: r["pct"] = round(0.85 * r["pct"] + 0.15 * v[0] * 100, 1); ai_notes[r["id"]] = f"conf={v[0]:.2f} missing: {v[1][:120]}"
        results.append(r)
        print(f" → {len(r['members'])} files · caps {r['cap_found']}/{len(r['caps'])} · {r['pct']}%")
    out = generate(results, prev, Path(args.output), ai_notes)
    print(f"\n✅ Matrix written: {out}\n✅ State saved:    {STATE_FILE}")
    return 0

if __name__ == "__main__":
    sys.exit(main())