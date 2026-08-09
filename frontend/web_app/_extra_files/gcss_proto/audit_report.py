import tinycss2, re, json, os
from collections import defaultdict

GLOBALS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\styles\globals.css"
BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_base.css"
UTIL = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_util.css"
OUT_JSON = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\globals_audit.json"
OUT_MD  = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\globals_audit.md"

RADIUS_TOKENS = {"sm":6,"md":8,"lg":12,"xl":16,"2xl":20,"3xl":24,"4xl":32}
def nearest_radius(px):
    best = min(RADIUS_TOKENS, key=lambda k: abs(RADIUS_TOKENS[k]-px))
    return f"rounded-{best} ({RADIUS_TOKENS[best]}px)"
DURATION_TOKENS = {150:"duration-150",200:"duration-200",300:"duration-300",500:"duration-500",700:"duration-700",1000:"duration-1000"}

# Brand palette (from theme.ts / tokens.css) for off-palette distance check
PALETTE = {
    "brand":"#2fb43d","brand-dark":"#1f8a2e","brand-light":"#5fd06f",
    "accent":"#ffd700","accent-light":"#ffe566","accent-dark":"#ccac00",
    "success":"#2fb43d","danger":"#ef4444","warning":"#f59e0b","info":"#3b82f6",
    "surface-0":"#0b0f14","surface-1":"#0f172a","surface-2":"#1e293b","surface-3":"#334155",
    "text":"#e7ecf3","text-muted":"#94a3b8","text-faint":"#64748b","border":"#1f2937",
    "white":"#ffffff","black":"#000000",
}
def hx(h):
    h=h.lstrip("#")
    if len(h)==3: h="".join(c*2 for c in h)
    try: return tuple(int(h[i:i+2],16) for i in (0,2,4))
    except: return None
def dist(a,b):
    return sum((a[i]-b[i])**2 for i in range(3))**0.5
def off_palette(hexstr):
    c=hx(hexstr)
    if not c: return "?"
    best=min(dist(c,hx(v)) for v in PALETTE.values() if hx(v))
    return "OFF" if best>60 else "ok"

def rule_sig(node):
    sel = " ".join(x.serialize() for x in node.prelude).strip()
    decls = tuple(sorted((d.lower_name, " ".join(v.serialize() for v in d.value).strip())
                         for d in node.content if d.type == "declaration"))
    return sel, decls

def index(path):
    idx = {}
    for t in tinycss2.parse_stylesheet(open(path, encoding="utf-8").read(), skip_whitespace=True):
        if t.type == "qualified-rule":
            s,d = rule_sig(t); idx.setdefault(s,set()).add(d)
        elif t.type == "at-rule" and t.content:
            for c in tinycss2.parse_rule_list(t.content, skip_whitespace=True):
                if c.type=="qualified-rule":
                    s,d = rule_sig(c); idx.setdefault(s,set()).add(d)
    return idx

base_idx, util_idx = index(BASE), index(UTIL)
def coverable(sel, decls):
    return (sel in base_idx and decls in base_idx[sel]) or (sel in util_idx and decls in util_idx[sel])

LINES = open(GLOBALS, encoding="utf-8").read().split("\n")

# Collect authored rule bodies (selector line .. closing brace) as raw text
authored = []  # {selector, line, text}
def walk(nodes):
    for t in nodes:
        if t.type == "qualified-rule":
            sel, decls = rule_sig(t)
            if not coverable(sel, decls):
                ln = getattr(t, "source_line", None)
                if ln and ln <= len(LINES):
                    # find closing brace from ln downward
                    depth = 0; end = ln; started = False
                    for i in range(ln-1, len(LINES)):
                        line = LINES[i]
                        depth += line.count("{") - line.count("}")
                        started = True
                        if started and depth <= 0 and "}" in line:
                            end = i+1; break
                    body = "\n".join(LINES[ln-1:end]).strip()
                    authored.append({"selector": sel, "line": ln, "text": body})
        elif t.type == "at-rule" and t.content:
            walk(tinycss2.parse_rule_list(t.content, skip_whitespace=True))
walk(tinycss2.parse_stylesheet(open(GLOBALS, encoding="utf-8").read(), skip_whitespace=True))

px_re = re.compile(r'(?<![-\w.])(\d+(?:\.\d+)?)px(?![-\w])')
hex_re = re.compile(r'#([0-9a-fA-F]{3,8})\b')

px_agg=defaultdict(list); radius_agg=defaultdict(list); shadow=[]
hex_agg=defaultdict(list); dur_agg=defaultdict(list); fs_agg=defaultdict(list)
for r in authored:
    txt = r["text"]; ln = r["line"]
    # only count if this source line actually declares something in this rule (best-effort)
    for m in px_re.findall(txt): px_agg[float(m)].append(ln)
    # border-radius detection
    if re.search(r'border-radius\s*:', txt):
        for m in px_re.findall(txt): radius_agg[float(m)].append(ln)
    if re.search(r'box-shadow\s*:', txt): shadow.append({"line":ln,"selector":r["selector"],"value":txt.strip()[:140]})
    for m in hex_re.findall(txt): hex_agg[m.lower()].append(ln)
    dm = re.search(r'(?:transition-duration|animation-duration)\s*:\s*(\d+)ms', txt)
    if dm: dur_agg[int(dm.group(1))].append(ln)
    fm = re.search(r'font-size\s*:\s*(\d+(?:\.\d+)?)px', txt)
    if fm: fs_agg[float(fm.group(1))].append(ln)

def compact(lst): return sorted(set(int(x) for x in lst))

px_report=[{"px":v,"count":len(px_agg[v]),"lines":compact(px_agg[v])[:8]} for v in sorted(px_agg, key=lambda x:-len(px_agg[x]))]
radius_report=[{"px":v,"token":nearest_radius(v),"count":len(radius_agg[v]),"lines":compact(radius_agg[v])[:6]} for v in sorted(radius_agg)]
hex_report=[{"hex":"#"+h,"count":len(hex_agg[h]),"lines":compact(hex_agg[h])[:6]} for h in sorted(hex_agg, key=lambda x:-len(hex_agg[x]))]
dur_report=[{"ms":d,"token":DURATION_TOKENS.get(d,"(MISSING)"),"count":len(dur_agg[d]),"lines":compact(dur_agg[d])[:6]} for d in sorted(dur_agg)]
fs_report=[{"px":f,"count":len(fs_agg[f]),"lines":compact(fs_agg[f])[:6]} for f in sorted(fs_agg)]

summary={
 "authored_rule_count":len(authored),
 "distinct_px":len(px_agg),"total_px":sum(len(v) for v in px_agg.values()),
 "distinct_radius":len(radius_agg),"distinct_hex":len(hex_agg),"total_hex":sum(len(v) for v in hex_agg.values()),
 "shadow_decls":len(shadow),"distinct_durations":sorted(dur_agg),"distinct_fontsize_px":sorted(fs_agg),
}
report={"summary":summary,"px_report":px_report,"radius_report":radius_report,"hex_report":hex_report,
        "duration_report":dur_report,"fontsize_report":fs_report,"shadow_sample":shadow[:30]}
json.dump(report, open(OUT_JSON,"w"), indent=2)

md=["# globals.css Authored-CSS Audit (DS08/DS09/DS11/DS03/DS16)","","Source: `frontend/web_app/src/styles/globals.css`",""]
md.append("## Summary")
for k,v in summary.items(): md.append(f"- **{k}**: {v}")
md.append("")
md.append("## Border-radius (DS09) — target ≤5 tokens")
md.append("| px | proposed token | count | sample lines |")
for r in radius_report: md.append(f"| {r['px']} | {r['token']} | {r['count']} | {r['lines']} |")
md.append("")
md.append(f"## box-shadow (DS11) — target ≤4 elevation tokens (total {len(shadow)})")
for s in shadow[:15]: md.append(f"- L{s['line']} `{s['selector'][:36]}`: `{s['value']}...`")
md.append("")
md.append("## Durations (DS16)")
md.append("| ms | token | count |")
for d in dur_report: md.append(f"| {d['ms']} | {d['token']} | {d['count']} |")
md.append("")
md.append("## Font-size px (DS07)")
md.append("| px | count |")
for f in fs_report: md.append(f"| {f['px']} | {f['count']} |")
md.append("")
md.append("## Hex/rgba literals (DS03) — top by frequency  [flag: OFF = off-palette vs brand tokens]")
md.append("| hex | count | flag | sample lines |")
for h in hex_report[:30]:
    flag = off_palette(h["hex"])
    md.append(f"| {h['hex']} | {h['count']} | {flag} | {h['lines']} |")
md.append("")
md.append("## Raw px values (DS08) — top by frequency")
md.append("| px | count | sample lines |")
for p in px_report[:40]: md.append(f"| {p['px']} | {p['count']} | {p['lines']} |")
open(OUT_MD,"w",encoding="utf-8").write("\n".join(md))
print("WROTE")
print(json.dumps(summary, indent=2))
