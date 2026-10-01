import tinycss2, json, io, re, os

GLOBALS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\styles\globals.css"
BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_base.css"
UTIL = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_util.css"
COMP = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\globals_regen.css"

def rule_sig(node):
    sel = " ".join(x.serialize() for x in node.prelude).strip()
    decls = tuple(sorted((d.lower_name, " ".join(v.serialize() for v in d.value).strip())
                         for d in node.content if d.type == "declaration"))
    return sel, decls

def index(path):
    text = open(path, encoding="utf-8").read()
    toks = tinycss2.parse_stylesheet(text, skip_whitespace=True)
    idx = {}
    for t in toks:
        if t.type == "qualified-rule":
            sel, decls = rule_sig(t)
            idx.setdefault(sel, set()).add(decls)
        elif t.type == "at-rule" and t.content:
            for c in tinycss2.parse_rule_list(t.content, skip_whitespace=True):
                if c.type == "qualified-rule":
                    sel, decls = rule_sig(c)
                    idx.setdefault(sel, set()).add(decls)
    return idx

base_idx = index(BASE)
util_idx = index(UTIL)

def is_coverable(sel, decls):
    return (sel in base_idx and decls in base_idx[sel]) or (sel in util_idx and decls in util_idx[sel])

# Parse globals.css and rebuild: keep only rules NOT coverable by base/util.
gtext = open(GLOBALS, encoding="utf-8").read()
gtoks = tinycss2.parse_stylesheet(gtext, skip_whitespace=True)

def keep_rule(node):
    sel, decls = rule_sig(node)
    return not is_coverable(sel, decls)

def rebuild(nodes):
    out = []
    for t in nodes:
        if t.type in ("whitespace", "comment"):
            # drop comments from compiled dump; keep none
            continue
        if t.type == "qualified-rule":
            if keep_rule(t):
                out.append(t)
        elif t.type == "at-rule":
            if t.lower_at_keyword in ("media", "supports", "layer") and t.content:
                inner = tinycss2.parse_rule_list(t.content, skip_whitespace=True)
                kept = rebuild(inner)
                if kept:
                    # re-emit at-rule with kept inner
                    pre = " ".join(x.serialize() for x in t.prelude)
                    inner_css = "".join(serialize_node(k) for k in kept)
                    out.append(("at", t.lower_at_keyword, pre, inner_css))
            else:
                # non-media at-rules (keyframes, font-face, etc.) -> keep if not coverable
                # keyframes won't be in base/util (they're custom). keep.
                out.append(t)
        else:
            out.append(t)
    return out

def serialize_node(n):
    if isinstance(n, tuple) and n[0] == "at":
        return f"@{n[1]} {n[2]} {{" + n[3] + "}}"
    return n.serialize()

kept = rebuild(gtoks)

# Count
n_kept_rules = 0
n_kept_media = 0
custom_classes = []
for n in kept:
    if isinstance(n, tuple) and n[0] == "at":
        n_kept_media += 1
    elif hasattr(n, "type") and n.type == "qualified-rule":
        n_kept_rules += 1
        sel = " ".join(x.serialize() for x in n.prelude).strip()
        if re.match(r'^\.[A-Za-z]', sel.replace('\\','')):
            custom_classes.append(sel)
    elif hasattr(n, "type") and n.type == "at-rule":
        # keyframes etc
        n_kept_rules += 1

with io.open(COMP, "w", encoding="utf-8") as f:
    for n in kept:
        f.write(serialize_node(n))

orig_lines = sum(1 for _ in open(GLOBALS, encoding="utf-8"))
comp_lines = sum(1 for _ in open(COMP, encoding="utf-8"))
orig_size = os.path.getsize(GLOBALS)
comp_size = os.path.getsize(COMP)

print(json.dumps({
    "orig_lines": orig_lines,
    "orig_bytes": orig_size,
    "regen_kept_lines": comp_lines,
    "regen_kept_bytes": comp_size,
    "removed_lines": orig_lines - comp_lines,
    "removed_pct": round(100*(orig_lines-comp_lines)/orig_lines, 1),
    "kept_top_rules": n_kept_rules,
    "kept_media_blocks": n_kept_media,
    "custom_class_count": len(custom_classes),
    "custom_class_sample": custom_classes[:40],
}, indent=2))
