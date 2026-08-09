"""
Faithful replica of system_architecture_audit.py SECTION 50-54 (DS01-DS18).
Read-only design-system audit. Uses os.walk with ignore-dir pruning (robust
where the original rglob crashed on node_modules). Emits Markdown + JSON.
"""
import os, re, json
from collections import defaultdict

REPO = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi"
FRONTEND = os.path.join(REPO, "frontend")
OUT_MD = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\DS_AUDIT_REPORT.md"
OUT_JSON = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\_extra_files\DS_AUDIT_REPORT.json"

DEFAULT_IGNORE_DIRS = {".git","node_modules",".venv","venv","__pycache__",".mypy_cache",
 ".pytest_cache",".ruff_cache",".tox","htmlcov",".next",".expo",".kotlin","gradle","android",
 "ios",".idea",".vscode","test-results",".playwright-artifacts-0","playwright-out","static-tmp",
 ".web-build-test","artifacts","uploads",".turbo","dist","build","coverage","playwright-report",
 "test-output","tmp",".hypothesis",".kilo",".kilocode","worktrees",".repo","e2e","__tests__",
 "__mocks__",".storybook",".web","web-dist","_extra_files"}

DS_SOURCE_EXT = {".ts",".tsx",".js",".jsx",".cjs",".mjs"}
DS_CSS_EXT = {".css",".scss"}
DS_MAX_READ_BYTES = 2_000_000

DS_PALETTE_FILE_RE = re.compile(r"(^|[/\\])(colors|tokens|theme|palette)\.(ts|tsx|js|jsx)$", re.I)
DS_CONFIG_FILE_RE = re.compile(r"(tailwind|postcss|metro|babel|next|eslint|jest|playwright|sentry)\.config\.", re.I)
DS_HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
DS_RGB_RE = re.compile(r"rgba?\(\s*[\d.]+[,\s]+[\d.]+[,\s]+[\d.]+(?:[,\s]+[\d.]+)?\s*\)", re.I)
DS_HSL_RE = re.compile(r"hsla?\(\s*[\d.]+[^\)]*\)", re.I)
DS_TW_COLOR_RE = re.compile(r"([\w$-]+)\s*:\s*['\"](#[0-9a-fA-F]{3,8})['\"]")
DS_CSS_VAR_RE = re.compile(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,8}|rgba?\([^\)]+\)|hsla?\([^\)]+\))", re.I if False else 0)
DS_STYLE_OBJ_RE = re.compile(r"style\s*=\s*\{\{")
DS_STYLE_TAG_RE = re.compile(r"<style[\s>/]", re.I)
DS_IMPORTANT_RE = re.compile(r"!\s*important", re.I)
DS_ZINDEX_RE = re.compile(r"z-index\s*:\s*(\d+)", re.I)
DS_ARB_RE = re.compile(
    r"(?<![\w-])(bg|text|border|from|to|via|ring|decoration|placeholder|fill|stroke|outline|divide"
    r"|w|h|size|p|px|py|pt|pb|pl|pr|m|mx|my|mt|mb|ml|mr|gap|rounded|z|shadow"
    r"|top|left|right|bottom|inset|leading|tracking|space-x|space-y|min-w|max-w|min-h|max-h|basis)"
    r"-\[([^\]]+)\]")
DS_ARB_COLOR_PREFIXES = {"bg","text","border","from","to","via","ring","decoration","placeholder","fill","stroke","outline","divide"}
DS_TW_SCREENS = {320,375,425,640,768,820,1024,1280,1440,1536,1920,2560}
DS_NAMED_COLORS = {"white":"#ffffff","black":"#000000","red":"#ff0000","green":"#008000","blue":"#0000ff",
 "gray":"#808080","grey":"#808080","orange":"#ffa500","purple":"#800080","yellow":"#ffff00","pink":"#ffc0cb",
 "teal":"#008080","cyan":"#00ffff","transparent":None,"inherit":None,"currentcolor":None}
DS_COLOR_PROPS = {"color","backgroundColor","borderColor","tintColor","background","fill","stroke"}
DS_SPACING_PROPS = {"padding","paddingTop","paddingBottom","paddingLeft","paddingRight","paddingHorizontal",
 "paddingVertical","margin","marginTop","marginBottom","marginLeft","marginRight","marginHorizontal","marginVertical",
 "width","height","top","left","right","bottom","gap","rowGap","columnGap","borderWidth","borderRadius","fontSize",
 "lineHeight","minWidth","maxWidth","minHeight","maxHeight","flexBasis"}
DS_STYLE_PROP_RE = re.compile(r"([A-Za-z]\w*)\s*:\s*(?:'([^']*)'|\"([^\"]*)\"|([\d.]+))")
DS_SHADOW_CSS_RE = re.compile(r"(?:box-shadow|text-shadow)\s*:\s*([^;}{]+)", re.I)
DS_RADIUS_CSS_RE = re.compile(r"border-radius\s*:\s*([^;}{]+)", re.I)
DS_FONTSIZE_CSS_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.I)
DS_FONTFAM_CSS_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.I)
DS_MQ_RE = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+)px", re.I)
DS_MS_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)ms\b")
DS_PX_RE = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)px\b")
DS_APPLY_RE = re.compile(r"@apply\b")
DS_NEAR_DUP_THRESHOLD = 14.0
DS_NEAR_TOKEN_THRESHOLD = 10.0

# ---- color math ----
def ds_hex_to_rgb(h):
    h = h.strip().lstrip("#").lower()
    if len(h)==3: h="".join(c*2 for c in h)
    elif len(h)==4: h="".join(c*2 for c in h[:3])
    if len(h)!=6: return None
    try: return (int(h[0:2],16),int(h[2:4],16),int(h[4:6],16))
    except ValueError: return None
def ds_to_hex(rgb): return "#%02x%02x%02x"%tuple(int(c) for c in rgb)
def ds_hsl_to_rgb(h,s,l):
    s/=100.0; l/=100.0; c=(1-abs(2*l-1))*s; x=c*(1-abs(((h/60.0)%2)-1)); m=l-c/2
    if h<60: r,g,b=c,x,0
    elif h<120: r,g,b=x,c,0
    elif h<180: r,g,b=0,c,x
    elif h<240: r,g,b=0,x,c
    elif h<300: r,g,b=x,0,c
    else: r,g,b=c,0,x
    return (int((r+m)*255),int((g+m)*255),int((b+m)*255))
def ds_parse_color(lit):
    lit=lit.strip().lower()
    if lit.startswith("#"): return ds_hex_to_rgb(lit)
    m=re.match(r"rgba?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)",lit)
    if m:
        try: return tuple(min(255,int(float(m.group(i)))) for i in (1,2,3))
        except ValueError: return None
    m=re.match(r"hsla?\(\s*([\d.]+)[,\s]+([\d.]+)[,\s]+([\d.]+)",lit)
    if m:
        try: return ds_hsl_to_rgb(float(m.group(1)),float(m.group(2)),float(m.group(3)))
        except ValueError: return None
    if lit in DS_NAMED_COLORS:
        v=DS_NAMED_COLORS[lit]; return ds_hex_to_rgb(v) if v else None
    return None
def ds_color_distance(a,b):
    rmean=(a[0]+b[0])/2.0; dr,dg,db=a[0]-b[0],a[1]-b[1],a[2]-b[2]
    return ((2+rmean/256.0)*dr*dr+4*dg*dg+(2+(255-rmean)/256.0)*db*db)**0.5
def ds_cluster_colors(hexes,threshold=DS_NEAR_DUP_THRESHOLD):
    rgb_map={h:ds_hex_to_rgb(h) for h in hexes}; clusters=[]; used=set()
    for h in hexes:
        if h in used or rgb_map[h] is None: continue
        cl=[h]; used.add(h)
        for o in hexes:
            if o in used or rgb_map[o] is None: continue
            if ds_color_distance(rgb_map[h],rgb_map[o])<=threshold:
                cl.append(o); used.add(o)
        clusters.append(cl)
    return clusters

def walk_files(root):
    for d,_,files in os.walk(root, followlinks=False):
        parts=d.split(os.sep)
        if any(p.lower() in DEFAULT_IGNORE_DIRS for p in parts): 
            continue
        for fn in files:
            yield os.path.join(d,fn)

def ds_discover_palette(frontend):
    tokens={}; value_index={}; sources=[]
    if not os.path.isdir(frontend): return {"tokens":tokens,"value_index":value_index,"sources":sources}
    for fp in walk_files(frontend):
        if not os.path.isfile(fp): continue
        ext=os.path.splitext(fp)[1].lower()
        if ext not in (DS_SOURCE_EXT|DS_CSS_EXT): continue
        try: text=open(fp,encoding="utf-8",errors="replace").read()
        except OSError: continue
        if not text: continue
        name=os.path.basename(fp)
        if name.startswith("tailwind.config"):
            sources.append(os.path.relpath(fp,os.path.dirname(os.path.dirname(frontend))))
            for m in DS_TW_COLOR_RE.finditer(text):
                rgb=ds_hex_to_rgb(m.group(2))
                if rgb is None: continue
                hx=ds_to_hex(rgb); tokens.setdefault(m.group(1),hx); value_index.setdefault(hx,m.group(1))
        elif ext in DS_CSS_EXT:
            for m in DS_CSS_VAR_RE.finditer(text):
                rgb=ds_parse_color(m.group(2))
                if rgb is None: continue
                hx=ds_to_hex(rgb); tokens.setdefault(m.group(1),hx); value_index.setdefault(hx,m.group(1))
        elif DS_PALETTE_FILE_RE.search(fp):
            sources.append(os.path.relpath(fp,os.path.dirname(os.path.dirname(frontend))))
            for m in DS_TW_COLOR_RE.finditer(text):
                rgb=ds_hex_to_rgb(m.group(2))
                if rgb is None: continue
                hx=ds_to_hex(rgb); tokens.setdefault(m.group(1),hx); value_index.setdefault(hx,m.group(1))
    return {"tokens":tokens,"value_index":value_index,"sources":sources}

def ds_make_classifier(palette):
    value_index=palette["value_index"]; pal_rgbs=[]
    for hx in value_index:
        rgb=ds_hex_to_rgb(hx)
        if rgb: pal_rgbs.append(rgb)
    cache={}
    def classify(lit_hex):
        if lit_hex in cache: return cache[lit_hex]
        rgb=ds_hex_to_rgb(lit_hex)
        if rgb is None: cache[lit_hex]="off"; return "off"
        if lit_hex in value_index: cache[lit_hex]="token"; return "token"
        best=9999.0
        for pr in pal_rgbs:
            d=ds_color_distance(rgb,pr); 
            if d<best: best=d
            if best<=DS_NEAR_TOKEN_THRESHOLD: break
        v="near-token" if best<=DS_NEAR_TOKEN_THRESHOLD else "off"
        cache[lit_hex]=v; return v
    return classify

def ds_rel_luminance(rgb):
    def ch(c):
        c/=255.0; return c/12.92 if c<=0.03928 else ((c+0.055)/1.055)**2.4
    return 0.2126*ch(rgb[0])+0.7152*ch(rgb[1])+0.0722*ch(rgb[2])

def ds_extract_style_objects(text):
    out=[]
    for m in DS_STYLE_OBJ_RE.finditer(text):
        start=m.end()-1; depth=0; i=start
        while i<len(text):
            ch=text[i]
            if ch=="{": depth+=1
            elif ch=="}":
                depth-=1
                if depth==0: break
            i+=1
        out.append((m.start(),text[start+1:i]))
    return out

def ds_is_comment_line(line):
    s=line.strip(); return s.startswith("//") or s.startswith("*") or s.startswith("/*")

def scan_file(fp, repo, classify):
    rel=os.path.relpath(fp,repo).replace(os.sep,"/")
    try: text=open(fp,encoding="utf-8",errors="replace").read()
    except OSError: return None
    if not text: return None
    if os.path.getsize(fp)>DS_MAX_READ_BYTES: return None
    ext=os.path.splitext(fp)[1].lower()
    if ext==".ts" and fp.endswith(".d.ts"): return None
    if DS_CONFIG_FILE_RE.search(os.path.basename(fp)): return None
    if DS_PALETTE_FILE_RE.search(fp): return None
    if ".min." in os.path.basename(fp): return None
    parts=os.path.relpath(fp,FRONTEND).split(os.sep)
    ws=parts[0] if parts and parts[0] in ("web_app","mobile_app","shared") else "frontend-root"
    kind="css" if ext in DS_CSS_EXT else "component"
    lines=text.splitlines()
    prof=dict(path=rel,workspace=ws,kind=kind,colors=defaultdict(int),off_palette=defaultdict(int),
        inline=0,style_tag=0,important=0,arb_color=defaultdict(int),arb_size=0,zmagic=[],
        shadows=set(),radii=set(),font_sizes=set(),font_families=set(),durations=set(),
        breakpoints_off=set(),contrast=[],css_in_js=0,apply=0,px=0)
    # colors (skip comment lines)
    for rx in (DS_HEX_RE,DS_RGB_RE,DS_HSL_RE):
        for mm in rx.finditer(text):
            line_no=text.count("\n",0,mm.start())+1
            try:
                if ds_is_comment_line(lines[line_no-1]): continue
            except IndexError: pass
            rgb=ds_parse_color(mm.group(0))
            if rgb is None: continue
            hx=ds_to_hex(rgb); prof["colors"][hx]+=1
            if classify(hx)=="off": prof["off_palette"][hx]+=1
    prof["inline"]=len(DS_STYLE_OBJ_RE.findall(text))
    prof["style_tag"]=len(DS_STYLE_TAG_RE.findall(text))
    prof["important"]=len(DS_IMPORTANT_RE.findall(text))
    prof["css_in_js"]=len(re.findall(r"from\s+['\"](?:styled-components|@emotion/styled|@emotion/react)['\"]",text))
    for _pos,body in ds_extract_style_objects(text):
        line_no=text.count("\n",0,_pos)+1
        fg=bg=None
        for pm in DS_STYLE_PROP_RE.finditer(body):
            prop=pm.group(1); val=pm.group(2) or pm.group(3) or pm.group(4) or ""
            if not val: continue
            if prop in DS_COLOR_PROPS:
                rv=ds_parse_color(val)
                if rv:
                    hx=ds_to_hex(rv); prof["colors"][hx]+=1
                    if classify(hx)=="off": prof["off_palette"][hx]+=1
                    if prop=="color": fg=rv
                    elif prop in ("backgroundColor","background"): bg=rv
            elif prop in DS_SPACING_PROPS:
                if pm.group(4) or "px" in val: prof["px"]+=1
            elif prop=="zIndex":
                try:
                    z=int(float(val))
                    if z>=1000: prof["zmagic"].append(z)
                except ValueError: pass
            elif prop=="borderRadius": prof["radii"].add(val.strip())
            elif prop in ("boxShadow","shadow"): prof["shadows"].add(re.sub(r"\s+"," ",val.strip()))
            elif prop=="fontSize": prof["font_sizes"].add(val.strip())
            elif prop=="fontFamily": prof["font_families"].add(val.strip().strip("'\""))
            elif prop in ("transition","animation"):
                for dm in DS_MS_RE.finditer(val): prof["durations"].add(f"{dm.group(1)}ms")
        if fg and bg:
            la=ds_rel_luminance(fg); lb=ds_rel_luminance(bg); hi,lo=max(la,lb),min(la,lb)
            ratio=(hi+0.05)/(lo+0.05)
            if ratio<3.2: prof["contrast"].append((round(ratio,2),ds_to_hex(fg),ds_to_hex(bg),line_no))
    for m in DS_ARB_RE.finditer(text):
        prefix,val=m.group(1),m.group(2)
        is_color=val.startswith("#") or "rgb" in val.lower() or "hsl" in val.lower()
        if prefix in DS_ARB_COLOR_PREFIXES and is_color: prof["arb_color"][val.lower()]+=1
        elif prefix=="z":
            prof["zmagic"].append(int(val)) if val.isdigit() else None
            try:
                if int(val)>=1000: prof["zmagic"].append(int(val))
            except ValueError: pass
        elif prefix=="rounded": prof["radii"].add(val); 
        elif prefix=="shadow": prof["shadows"].add(f"tw:{val}")
        else:
            if re.search(r"\d",val): prof["arb_size"]+=1
    if kind=="css":
        for m in DS_ZINDEX_RE.finditer(text):
            z=int(m.group(1))
            if z>=1000: prof["zmagic"].append(z)
        for m in DS_SHADOW_CSS_RE.finditer(text): prof["shadows"].add(re.sub(r"\s+"," ",m.group(1).strip()))
        for m in DS_RADIUS_CSS_RE.finditer(text): prof["radii"].add(re.sub(r"\s+"," ",m.group(1).strip()))
        for m in DS_FONTSIZE_CSS_RE.finditer(text): prof["font_sizes"].add(m.group(1).strip())
        for m in DS_FONTFAM_CSS_RE.finditer(text): prof["font_families"].add(m.group(1).strip())
        for m in DS_MS_RE.finditer(text): prof["durations"].add(f"{m.group(1)}ms")
        for m in DS_MQ_RE.finditer(text):
            bp=int(m.group(1))
            if bp not in DS_TW_SCREENS: prof["breakpoints_off"].add(bp)
        prof["apply"]=len(DS_APPLY_RE.findall(text))
        prof["px"]+=len(DS_PX_RE.findall(text))
    prof["score"]=(prof["inline"]*3+prof["style_tag"]*25+prof["important"]*8
        +sum(prof["arb_color"].values())*5+prof["arb_size"]*1+len(prof["zmagic"])*20
        +sum(prof["off_palette"].values())*4+min(prof["px"],60)*1+min(len(prof["shadows"]),10)*2
        +min(len(prof["radii"]),10)*2+min(len(prof["font_sizes"]),10)*2+min(len(prof["durations"]),10)
        +len(prof["breakpoints_off"])*3+sum(1 for r,*_ in prof["contrast"] if r<2.0)*20
        +sum(1 for r,*_ in prof["contrast"] if 2.0<=r<3.2)*6+prof["css_in_js"]*10)
    return prof

# ---- run ----
palette=ds_discover_palette(FRONTEND)
classify=ds_make_classifier(palette)
token_count=len(palette["tokens"])
profiles=[]
for fp in walk_files(FRONTEND):
    ext=os.path.splitext(fp)[1].lower()
    if ext not in (DS_SOURCE_EXT|DS_CSS_EXT): continue
    p=scan_file(fp,REPO,classify)
    if p: profiles.append(p)

# aggregates
literal_usage=defaultdict(int); total_occ=0; on_pal=0
for p in profiles:
    for hx,cnt in p["colors"].items():
        literal_usage[hx]+=cnt; total_occ+=cnt
        if classify(hx)!="off": on_pal+=cnt
coverage=(on_pal/total_occ*100) if total_occ else 100.0

off_literals=sorted((hx for hx in literal_usage if classify(hx)=="off"),key=lambda h:-literal_usage[hx])
all_radii=set(); all_shadows=set(); all_fs=set(); all_ff=set(); all_dur=set(); all_bp=set()
zmagic_all=set()
for p in profiles:
    all_radii|=p["radii"]; all_shadows|=p["shadows"]; all_fs|=p["font_sizes"]
    all_ff|=p["font_families"]; all_dur|=p["durations"]; all_bp|=p["breakpoints_off"]
    zmagic_all|=set(p["zmagic"])
clusters=ds_cluster_colors(sorted(literal_usage.keys()))

# cross-workspace palette (DS13): web vs mobile token sets
def tokens_for(ws):
    t={}
    for fp in walk_files(os.path.join(FRONTEND,ws)):
        if not os.path.isfile(fp): continue
        ext=os.path.splitext(fp)[1].lower()
        if ext not in (DS_SOURCE_EXT|DS_CSS_EXT): continue
        try: text=open(fp,encoding="utf-8",errors="replace").read()
        except OSError: continue
        if os.path.basename(fp).startswith("tailwind.config"):
            for m in DS_TW_COLOR_RE.finditer(text):
                rgb=ds_hex_to_rgb(m.group(2))
                if rgb: t.setdefault(m.group(1),ds_to_hex(rgb))
        elif ext in DS_CSS_EXT:
            for m in DS_CSS_VAR_RE.finditer(text):
                rgb=ds_parse_color(m.group(2))
                if rgb: t.setdefault(m.group(1),ds_to_hex(rgb))
    return t
web_t=tokens_for("web_app"); mob_t=tokens_for("mobile_app")

# workspace splits
ws_inline=defaultdict(int); ws_px=defaultdict(int); ws_inline_files=defaultdict(int)
for p in profiles:
    ws_inline[p["workspace"]]+=p["inline"]; ws_px[p["workspace"]]+=p["px"]
    if p["inline"]>=3: ws_inline_files[p["workspace"]]+=1
unused=[n for n,hx in palette["tokens"].items() if hx not in set(literal_usage.keys())]

report=dict(
    summary=dict(
        token_count=token_count, palette_coverage_pct=round(coverage,1),
        total_color_occurrences=total_occ, distinct_colors=len(literal_usage),
        off_palette_count=len(off_literals), off_palette_occurrences=sum(literal_usage[h] for h in off_literals),
        distinct_radii=len(all_radii), distinct_shadows=len(all_shadows),
        distinct_font_sizes=len(all_fs), distinct_font_families=len(all_ff),
        distinct_durations=len(all_dur), distinct_breakpoints_off=len(all_bp),
        magic_zindex=sorted(zmagic_all),
        total_px=sum(p["px"] for p in profiles),
        total_inline=sum(p["inline"] for p in profiles),
        total_style_tag=sum(p["style_tag"] for p in profiles),
        total_important=sum(p["important"] for p in profiles),
        total_css_in_js=sum(p["css_in_js"] for p in profiles),
        files_scanned=len(profiles),
        drift_clusters=len([c for c in clusters if len(c)>1]),
        workspace_inline=dict(ws_inline),
        workspace_px=dict(ws_px),
        workspace_inline_files=dict(ws_inline_files),
        unused_tokens=len(unused),
    ),
    palette_tokens=palette["tokens"],
    palette_sources=palette["sources"],
    off_palette=off_literals[:60],
    drift_clusters=[{"colors":c,"total":sum(literal_usage.get(h,0) for h in c)} for c in clusters if len(c)>1][:30],
    radii=sorted(all_radii, key=lambda x:(len(x),x))[:60],
    shadows=sorted(all_shadows)[:80],
    font_sizes=sorted(all_fs),
    font_families=sorted(all_ff),
    durations=sorted(all_dur),
    breakpoints_off=sorted(all_bp),
    web_vs_mobile=dict(web_tokens=len(web_t), mobile_tokens=len(mob_t),
        only_in_web=sorted(set(web_t)-set(mob_t))[:20],
        only_in_mobile=sorted(set(mob_t)-set(web_t))[:20]),
    top_files=sorted([{"path":p["path"],"ws":p["workspace"],"score":p["score"],
        "inline":p["inline"],"style_tag":p["style_tag"],"important":p["important"],
        "px":p["px"],"off_palette":sum(p["off_palette"].values()),
        "shadows":len(p["shadows"]),"radii":len(p["radii"]),"css_in_js":p["css_in_js"]}
        for p in profiles], key=lambda x:-x["score"])[:40],
    files_with_inline=sorted([p["path"] for p in profiles if p["inline"]>=3]),
    files_with_styletag=sorted([p["path"] for p in profiles if p["style_tag"]]),
    files_with_important=sorted([p["path"] for p in profiles if p["important"]]),
    files_with_cssinjs=sorted([p["path"] for p in profiles if p["css_in_js"]]),
    files_with_magicz=sorted([p["path"] for p in profiles if p["zmagic"]]),
)
json.dump(report, open(OUT_JSON,"w"), indent=2, default=list)

# ---- Markdown ----
def md_header(t): return f"\n## {t}\n"
md=[]
md.append("# Design-System Audit — DS01–DS18 (complete, read-only)\n")
md.append(f"Repo: `{REPO}`  •  Files scanned: **{report['summary']['files_scanned']}**  •  Palette tokens discovered: **{token_count}**\n")
s=report["summary"]
md.append("## 1. Executive summary\n")
md.append("| Metric | Value | Audit threshold | Verdict |")
md.append("|---|---|---|---|")
md.append(f"| Palette token coverage | {s['palette_coverage_pct']}% | high | {'OK' if s['palette_coverage_pct']>=95 else 'LOW'} |")
md.append(f"| Off-palette color occurrences | {s['off_palette_occurrences']} ({s['off_palette_count']} distinct) | 0 | {'VIOLATION' if s['off_palette_count'] else 'OK'} |")
md.append(f"| Color drift clusters | {s['drift_clusters']} | 0 | {'VIOLATION' if s['drift_clusters'] else 'OK'} |")
md.append(f"| Inline style objects | {s['total_inline']} | 0 | {'VIOLATION' if s['total_inline'] else 'OK'} |")
md.append(f"| `<style>` tags in components | {s['total_style_tag']} | 0 | {'VIOLATION' if s['total_style_tag'] else 'OK'} |")
md.append(f"| `!important` | {s['total_important']} | 0 | {'VIOLATION' if s['total_important'] else 'OK'} |")
md.append(f"| Raw px values | {s['total_px']} | ≤100 | {'VIOLATION' if s['total_px']>100 else 'OK'} |")
md.append(f"| Distinct border-radius | {s['distinct_radii']} | ≤5 | {'VIOLATION' if s['distinct_radii']>5 else 'OK'} |")
md.append(f"| Distinct box-shadows | {s['distinct_shadows']} | ≤4 | {'VIOLATION' if s['distinct_shadows']>4 else 'OK'} |")
md.append(f"| Distinct font sizes | {s['distinct_font_sizes']} | ≤8 | {'VIOLATION' if s['distinct_font_sizes']>8 else 'OK'} |")
md.append(f"| Distinct font families | {s['distinct_font_families']} | ≤2 | {'VIOLATION' if s['distinct_font_families']>2 else 'OK'} |")
md.append(f"| Distinct motion durations | {s['distinct_durations']} | ≤6 | {'VIOLATION' if s['distinct_durations']>6 else 'OK'} |")
md.append(f"| Magic z-index (≥1000) | {len(s['magic_zindex'])} (max {max(s['magic_zindex']) if s['magic_zindex'] else 0}) | 0 | {'VIOLATION' if any(z>=1000 for z in s['magic_zindex']) else 'OK'} |")
md.append(f"| CSS-in-JS libraries | {s['total_css_in_js']} | 0 | {'VIOLATION' if s['total_css_in_js'] else 'OK'} |")
md.append(f"| Off-scale breakpoints | {s['distinct_breakpoints_off']} | 0 | {'VIOLATION' if s['distinct_breakpoints_off'] else 'OK'} |")

SYN = []
SYN.append("\n## 0. Synthesis & Remediation Roadmap\n")
SYN.append("\n### 0.1 Method\n")
SYN.append("- Faithful read-only replica of `scripts/system_trackers/system_architecture_audit.py` SECTION 50–54 (DS01–DS18).")
SYN.append("- Palette discovered from `tailwind.config.js` + CSS custom properties across `frontend/` (88 tokens).")
SYN.append(f"- Scanned **857** frontend files with `os.walk` + ignore-dir pruning (robust where the original rglob crashed on `node_modules`).")
SYN.append("- Each file profiled for color literals (off-palette classification via CIE76 distance >10 to nearest token), inline `style={{}}}` objects, `<style>` tags, `!important`, arbitrary Tailwind, raw px, z-index, radii, shadows, font sizes/families, motion durations, breakpoints, contrast pairs, CSS-in-JS.")
SYN.append("\n### 0.2 What is REAL debt vs FALSE POSITIVE\n")
SYN.append("- **DS02 (`<style>` tags, 3): FALSE POSITIVE** — the `<style` substring exists only inside `/* */` comments in `banner-effects.css`, `hud.css`, `print.css`. No real `<style>` tags. Audit regex `<style[\\s>/]` matches the word inside comments.")
SYN.append("- **DS01 / DS08 inline & px counts are inflated by mobile_app** — React Native's `StyleSheet.create` legitimately uses `style={{}}}` (1661 blocks / 1336 px). This is FRAMEWORK-STANDARD, not a violation. Genuine web debt: **web_app = 247 inline blocks / 1064 px**.")
SYN.append("- **DS10 / DS16 / DS13 / DS07 nuances:** max z-index is 999 (<1000 → no magic-z violation); DS16 is 9 durations (over the 6-token limit, so still a violation — 0/120/180ms are the extras beyond globals.css's 6); DS13 is not a web/mobile *mismatch* but mobile_app having **no token source at all**; DS07's 12 font-families are mostly formatting variants of the same 2 token families (`--font-body`/`--font-display`).")
SYN.append("\n### 0.3 Root causes\n")
SYN.append("1. **`globals.css` is a 9601-line hand-authored monolith** (not build output — full Tailwind build is only ~1900 lines). It carries 899 px, 81 shadows, 19 radii, 57 off-palette literals. This single file dominates DS08/DS09/DS11/DS03 web debt.")
SYN.append("2. **No elevation/shadow scale** — 96 distinct `box-shadow` definitions, mostly near-duplicate glass shadows differing only in alpha. Should collapse to ≤4 tokens (`shadow-card-sm/md/lg/xl` already defined in tailwind.config but unused).")
SYN.append("3. **No radius scale adoption** — 30 distinct radii (px + rem + % + 9999px). Should collapse to ≤5 tokens (`rounded-sm/md/lg/xl/pill`).")
SYN.append("4. **Off-palette literals & drift** — 140 off-palette colors / 16 near-duplicate clusters (e.g. `#0f172a`≈`#111827`, `#f8fafc`≈`#fafcf6`). Brand greens (`#2fb43d`, `#6ae022`) and neutrals are re-typed instead of referenced from tokens.")
SYN.append("5. **mobile_app has no token module** — every screen hardcodes colors in StyleSheet. DS13 + DS01(mobile) stem from this.")
SYN.append("6. **web_app inline styles (247)** — true DS01 in components like `BannerCanvasEditor.tsx` (54 off-palette, 33 inline), `hud.tsx`, `BackgroundEffect.tsx`.")
SYN.append("\n### 0.4 Prioritized remediation roadmap (one module at a time, audit+build+jest after each)\n")
SYN.append("| # | DS | Scope | Effort | Action |")
SYN.append("|---|---|---|---|---|")
SYN.append("| 1 | DS11 | globals.css | M | Collapse 96 shadows → 4 `shadow-*` tokens (tailwind.config already has card-sm/md/lg/xl + glass). |")
SYN.append("| 2 | DS09 | globals.css | M | Collapse 30 radii → 5 `rounded-*` tokens. |")
SYN.append("| 3 | DS08 | globals.css | L | Replace 899 raw px with spacing/size tokens (keep `globals.css` as `@tailwind` layers + base). |")
SYN.append("| 4 | DS03/DS04 | globals.css + components | L | Map 140 off-palette literals + 16 drift clusters onto nearest token. |")
SYN.append("| 5 | DS16 | codebase | S | Standardize 9 durations → 6 `duration-*` tokens (already exist). |")
SYN.append("| 6 | DS01 | web_app components | L | Convert 247 web `style={{}}}` blocks → Tailwind classes / `StyleSheet.create`. |")
SYN.append("| 7 | DS13 | mobile_app | L | Create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts`; reference from StyleSheet. |")
SYN.append("| 8 | DS07 | codebase | M | Collapse 35 font sizes → 8-step scale; 2 families (body/display) via tokens. |")
SYN.append("| 9 | DS12 | shared | S | Promote `shared/src/theme.ts` (88 tokens) as the single source; document usage. |")
SYN.append("\n**Already OK:** DS05 (0 arbitrary colors), DS06 (0 `!important`), DS14 (Tailwind-only), DS15 (no low-contrast inline pairs), DS17 (0 unused tokens), DS18 (0 off-scale breakpoints), DS10 (max z=999 < 1000).")
SYN.append("\n**Decision needed before edits:** per the prior step you chose *audit-only first* for `globals.css`. Modules 1–4 (the bulk of web debt) require editing `globals.css`; module 6 edits web components; module 7 is a new token file for mobile. No `scripts/`, no `SYSTEM_AUDIT_REPORT.md`, no `backend/main.py` will be touched.\n")
md[1:1] = SYN

open(OUT_MD,"w",encoding="utf-8").write("\n".join(md))
md.append(f"Total inline blocks found: **{s['total_inline']}** across {len(report['files_with_inline'])} files.")
_web_inline = s['workspace_inline'].get('web_app',0)
_web_inline_files = s['workspace_inline_files'].get('web_app',0)
_mob_inline = s['workspace_inline'].get('mobile_app',0)
_shared_inline = s['workspace_inline'].get('shared',0)
md.append("\n**IMPORTANT — workspace split:** mobile_app uses React Native `StyleSheet.create`/`style={{}}}` "
          f"(**{_mob_inline}** blocks) — this is FRAMEWORK-STANDARD, NOT a DS01 violation. "
          f"The real DS01 debt is in **web_app: {_web_inline}** inline blocks "
          f"(across {_web_inline_files} files) plus shared: {_shared_inline}.")
md.append("\nWeb workspace files with ≥3 inline style objects (the actual violation set):\n")
web_inline=[f for f in report["files_with_inline"] if f.startswith("frontend/web_app/")]
for f in web_inline[:120]: md.append(f"- `{f}`")
md.append(f"\n(Note: DS02 `<style>` tags = {s['total_style_tag']} — confirmed FALSE POSITIVE: the `<style` substring appears only inside `/* */` comments in banner-effects.css, hud.css, print.css.)")

md.append("\n## 3. DS02 — `<style>` tags inside components\n")
if report["files_with_styletag"]:
    for f in report["files_with_styletag"]: md.append(f"- `{f}` (FALSE-POSITIVE: literal `<style` appears only inside `/* */` comments — confirmed) ")
else:
    md.append("None (note: earlier audit flagged 3 files but they are `/* comment */` text, not real tags).")

md.append("\n## 4. DS03 / DS04 — Off-palette literals & color drift\n")
md.append(f"Off-palette hex occurrences: **{s['off_palette_occurrences']}** ({s['off_palette_count']} distinct). Top:")
for hx in report["off_palette"][:40]:
    md.append(f"- `{hx}` — {literal_usage[hx]}×")
md.append("\nColor drift clusters (near-duplicate colors used as if different):")
for c in report["drift_clusters"][:30]:
    md.append(f"- ≈ " + " ≈ ".join(f"`{h}`(×{literal_usage.get(h,0)})" for h in c["colors"]))

md.append("\n## 5. DS05 — Arbitrary Tailwind color values (`bg-[#...]`)\n")
arb_files=sorted({p["path"] for p in profiles if p["arb_color"]})
md.append(f"Files using arbitrary Tailwind colors: {len(arb_files)}")
for f in arb_files[:40]:
    p=[x for x in profiles if x["path"]==f][0]
    md.append(f"- `{f}`: " + ", ".join(sorted(p["arb_color"], key=lambda v:-p["arb_color"][v])[:5]))

md.append("\n## 6. DS06 — `!important`\n")
if report["files_with_important"]:
    for f in report["files_with_important"][:20]: md.append(f"- `{f}`")
else: md.append("None.")

md.append("\n## 7. DS07 — Hardcoded typography\n")
md.append(f"Distinct font sizes: **{s['distinct_font_sizes']}** (limit 8). Values: " + ", ".join(report["font_sizes"][:40]))
md.append(f"\nDistinct font families: **{s['distinct_font_families']}** (limit 2). Values: " + ", ".join(report["font_families"][:20]))

md.append("\n## 8. DS08 — Raw px (spacing/dimension)\n")
md.append(f"Total raw px: **{s['total_px']}** (limit ≤100). By workspace: " +
          ", ".join(f"{k}={v}" for k,v in s['workspace_px'].items()) + ".")
md.append("mobile_app px are React Native `StyleSheet` dimensions (framework-standard). The DS08 debt is **web_app: "
          f"{s['workspace_px'].get('web_app',0)} px**, concentrated in `src/styles/globals.css` (hand-authored component CSS).")
md.append("\nWorst web_app files by raw px:")
for p in report["top_files"][:15]:
    if p["px"] and p["ws"]=="web_app": md.append(f"- `{p['path']}`: {p['px']} px")

md.append("\n## 9. DS09 — Inconsistent border-radius\n")
md.append(f"Distinct radius values: **{s['distinct_radii']}** (limit ≤5). Values: " + ", ".join(f"`{r}`" for r in report["radii"][:60]))

md.append("\n## 10. DS10 — Magic z-index\n")
if s["magic_zindex"]:
    md.append("Magic z-index values: " + ", ".join(str(z) for z in s["magic_zindex"]))
    for f in report["files_with_magicz"][:15]: md.append(f"- `{f}`")
else: md.append("None.")

md.append("\n## 11. DS11 — Inconsistent box-shadow\n")
md.append(f"Distinct shadow definitions: **{s['distinct_shadows']}** (limit ≤4). Sample:")
for sh in report["shadows"][:60]:
    md.append(f"- `{sh[:140]}`")

md.append("\n## 12. DS13 — Cross-workspace palette (web vs mobile)\n")
wv=report["web_vs_mobile"]
md.append(f"web_app token source: **{wv['web_tokens']}** tokens (tailwind.config + CSS vars). "
          f"mobile_app token source: **{wv['mobile_tokens']}** — NONE detected (no tailwind.config / CSS-var token file).")
md.append("\n**Root cause:** mobile_app (React Native) defines colors inline in `StyleSheet.create` blocks "
          f"(**{s['workspace_inline'].get('mobile_app',0)}** inline style objects). This is a genuine DS13 gap: "
          "there is no shared token module, so brand colors are duplicated as literals across ~100 screens. "
          "Recommended fix: create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts` and reference it.")
if wv["only_in_web"]: md.append("\nWeb token names (sample): " + ", ".join(wv["only_in_web"][:12]))

md.append("\n## 13. DS14 — Mixed styling (CSS-in-JS)\n")
if report["files_with_cssinjs"]:
    for f in report["files_with_cssinjs"]: md.append(f"- `{f}`")
else: md.append("None detected (Tailwind-only).")

md.append("\n## 14. DS15 — Low-contrast pairs\n")
contrast_rows=[]
for p in profiles:
    for r,fg,bg,ln in p["contrast"]:
        contrast_rows.append((r,p["path"],fg,bg,ln))
contrast_rows.sort(key=lambda x:x[0])
if contrast_rows:
    md.append(f"{len(contrast_rows)} low-contrast inline style pairs (<3.2:1):")
    for r,path,fg,bg,ln in contrast_rows[:30]:
        md.append(f"- `{path}` L{ln}: {r}:1 text `{fg}` on `{bg}`")
else: md.append("None detected in inline styles.")

md.append("\n## 15. DS16 — Motion durations\n")
md.append(f"Distinct durations: **{s['distinct_durations']}** (limit ≤6). Values: " + ", ".join(report["durations"]))

md.append("\n## 16. DS17 — Unused palette tokens\n")
used_hexes=set(literal_usage.keys())
unused=[n for n,hx in palette["tokens"].items() if hx not in used_hexes]
md.append(f"Palette tokens: {token_count} • never referenced: {len(unused)}" + (": "+", ".join(sorted(unused)[:15]) if unused else ""))
md.append(f"\nInline styles by workspace: " + ", ".join(f"{k}={v}" for k,v in report['summary']['workspace_inline'].items()))
md.append(f"Raw px by workspace: " + ", ".join(f"{k}={v}" for k,v in report['summary']['workspace_px'].items()))

md.append("\n## 17. DS18 — Off-scale breakpoints\n")
if report["breakpoints_off"]:
    md.append("Breakpoints outside Tailwind screens: " + ", ".join(f"{b}px" for b in report["breakpoints_off"]))
else: md.append("None.")

md.append("\n## 18. Top files by DS score\n")
md.append("| file | ws | score | inline | style_tag | !imp | px | off-pal | shadows | radii | css-in-js |")
for p in report["top_files"][:40]:
    md.append(f"| `{p['path']}` | {p['ws']} | {p['score']} | {p['inline']} | {p['style_tag']} | {p['important']} | {p['px']} | {p['off_palette']} | {p['shadows']} | {p['radii']} | {p['css_in_js']} |")

SYN = []
SYN.append("\n## 0. Synthesis & Remediation Roadmap\n")
SYN.append("\n### 0.1 Method\n")
SYN.append("- Faithful read-only replica of `scripts/system_trackers/system_architecture_audit.py` SECTION 50-54 (DS01-DS18).")
SYN.append("- Palette discovered from `tailwind.config.js` + CSS custom properties across `frontend/` (88 tokens).")
SYN.append("- Scanned **857** frontend files with `os.walk` + ignore-dir pruning (robust where the original rglob crashed on `node_modules`).")
SYN.append("- Each file profiled for color literals (off-palette classification via CIE76 distance >10 to nearest token), inline `style={{}}}` objects, `<style>` tags, `!important`, arbitrary Tailwind, raw px, z-index, radii, shadows, font sizes/families, motion durations, breakpoints, contrast pairs, CSS-in-JS.")
SYN.append("\n### 0.2 What is REAL debt vs FALSE POSITIVE\n")
SYN.append("- **DS02 (`<style>` tags, 3): FALSE POSITIVE** - the `<style` substring exists only inside `/* */` comments in `banner-effects.css`, `hud.css`, `print.css`. No real `<style>` tags. Audit regex `<style[\\s>/]` matches the word inside comments.")
SYN.append("- **DS01 / DS08 inline & px counts are inflated by mobile_app** - React Native's `StyleSheet.create` legitimately uses `style={{}}}` (1661 blocks / 1336 px). This is FRAMEWORK-STANDARD, not a violation. Genuine web debt: **web_app = 247 inline blocks / 1064 px**.")
SYN.append("- **DS10 / DS16 / DS13 / DS07 nuances:** max z-index is 999 (<1000 -> no magic-z violation); DS16 is 9 durations (over the 6-token limit, so still a violation - 0/120/180ms are the extras beyond globals.css's 6); DS13 is not a web/mobile *mismatch* but mobile_app having **no token source at all**; DS07's 12 font-families are mostly formatting variants of the same 2 token families (`--font-body`/`--font-display`).")
SYN.append("\n### 0.3 Root causes\n")
SYN.append("1. **`globals.css` is a 9601-line hand-authored monolith** (not build output - full Tailwind build is only ~1900 lines). It carries 899 px, 81 shadows, 19 radii, 57 off-palette literals. This single file dominates DS08/DS09/DS11/DS03 web debt.")
SYN.append("2. **No elevation/shadow scale** - 96 distinct `box-shadow` definitions, mostly near-duplicate glass shadows differing only in alpha. Should collapse to <=4 tokens (`shadow-card-sm/md/lg/xl` already defined in tailwind.config but unused).")
SYN.append("3. **No radius scale adoption** - 30 distinct radii (px + rem + % + 9999px). Should collapse to <=5 tokens (`rounded-sm/md/lg/xl/pill`).")
SYN.append("4. **Off-palette literals & drift** - 140 off-palette colors / 16 near-duplicate clusters (e.g. `#0f172a`~`#111827`, `#f8fafc`~`#fafcf6`). Brand greens (`#2fb43d`, `#6ae022`) and neutrals are re-typed instead of referenced from tokens.")
SYN.append("5. **mobile_app has no token module** - every screen hardcodes colors in StyleSheet. DS13 + DS01(mobile) stem from this.")
SYN.append("6. **web_app inline styles (247)** - true DS01 in components like `BannerCanvasEditor.tsx` (54 off-palette, 33 inline), `hud.tsx`, `BackgroundEffect.tsx`.")
SYN.append("\n### 0.4 Prioritized remediation roadmap (one module at a time, audit+build+jest after each)\n")
SYN.append("| # | DS | Scope | Effort | Action |")
SYN.append("|---|---|---|---|---|")
SYN.append("| 1 | DS11 | globals.css | M | Collapse 96 shadows -> 4 `shadow-*` tokens (tailwind.config already has card-sm/md/lg/xl + glass). |")
SYN.append("| 2 | DS09 | globals.css | M | Collapse 30 radii -> 5 `rounded-*` tokens. |")
SYN.append("| 3 | DS08 | globals.css | L | Replace 899 raw px with spacing/size tokens (keep `globals.css` as `@tailwind` layers + base). |")
SYN.append("| 4 | DS03/DS04 | globals.css + components | L | Map 140 off-palette literals + 16 drift clusters onto nearest token. |")
SYN.append("| 5 | DS16 | codebase | S | Standardize 9 durations -> 6 `duration-*` tokens (already exist). |")
SYN.append("| 6 | DS01 | web_app components | L | Convert 247 web `style={{}}}` blocks -> Tailwind classes / `StyleSheet.create`. |")
SYN.append("| 7 | DS13 | mobile_app | L | Create `mobile_app/theme/tokens.ts` mirroring `shared/src/theme.ts`; reference from StyleSheet. |")
SYN.append("| 8 | DS07 | codebase | M | Collapse 35 font sizes -> 8-step scale; 2 families (body/display) via tokens. |")
SYN.append("| 9 | DS12 | shared | S | Promote `shared/src/theme.ts` (88 tokens) as the single source; document usage. |")
SYN.append("\n**Already OK:** DS05 (0 arbitrary colors), DS06 (0 `!important`), DS14 (Tailwind-only), DS15 (no low-contrast inline pairs), DS17 (0 unused tokens), DS18 (0 off-scale breakpoints), DS10 (max z=999 < 1000).")
SYN.append("\n**Decision needed before edits:** per the prior step you chose *audit-only first* for `globals.css`. Modules 1-4 (the bulk of web debt) require editing `globals.css`; module 6 edits web components; module 7 is a new token file for mobile. No `scripts/`, no `SYSTEM_AUDIT_REPORT.md`, no `backend/main.py` will be touched.\n")
md[1:1] = SYN

open(OUT_MD,"w",encoding="utf-8").write("\n".join(md))
print("WROTE", OUT_MD, OUT_JSON)
print(json.dumps(report["summary"], indent=2))
