import tinycss2, re, json, os
from collections import Counter

GLOBALS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\styles\globals.css"
BASE = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_base.css"
UTIL = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen_util.css"

def rule_sig(node):
    sel = " ".join(x.serialize() for x in node.prelude).strip()
    decls = tuple(sorted((d.lower_name, " ".join(v.serialize() for v in d.value).strip())
                         for d in node.content if d.type == "declaration"))
    return sel, decls

def index(path):
    idx = {}
    toks = tinycss2.parse_stylesheet(open(path, encoding="utf-8").read(), skip_whitespace=True)
    for t in toks:
        if t.type == "qualified-rule":
            s, d = rule_sig(t); idx.setdefault(s, set()).add(d)
        elif t.type == "at-rule" and t.content:
            for c in tinycss2.parse_rule_list(t.content, skip_whitespace=True):
                if c.type == "qualified-rule":
                    s, d = rule_sig(c); idx.setdefault(s, set()).add(d)
    return idx

base_idx, util_idx = index(BASE), index(UTIL)

def coverable(sel, decls):
    return (sel in base_idx and decls in base_idx[sel]) or (sel in util_idx and decls in util_idx[sel])

# Walk globals; a rule is "authored" if not coverable. Collect authored rules.
authored = []  # (selector, body_text)
def walk(nodes):
    for t in nodes:
        if t.type == "qualified-rule":
            sel, decls = rule_sig(t)
            if not coverable(sel, decls):
                body = " ".join(x.serialize() for x in t.content if x.type != "whitespace").strip()
                authored.append((sel, body))
        elif t.type == "at-rule" and t.content:
            if t.lower_at_keyword in ("media", "supports", "layer"):
                walk(tinycss2.parse_rule_list(t.content, skip_whitespace=True))
            else:
                # keyframes/font-face etc -> authored
                body = " ".join(x.serialize() for x in t.content if x.type != "whitespace").strip()
                authored.append(("@" + t.lower_at_keyword + " " + " ".join(x.serialize() for x in t.prelude), body))

walk(tinycss2.parse_stylesheet(open(GLOBALS, encoding="utf-8").read(), skip_whitespace=True))

# Now measure hardcoded values in authored bodies
px_re = re.compile(r'(?<![-\w])(\d+(?:\.\d+)?)px(?![-\w])')
hex_re = re.compile(r'#([0-9a-fA-F]{3,8})\b')
shadow_re = re.compile(r'box-shadow\s*:', re.I)
radius_re = re.compile(r'border-radius\s*:', re.I)
duration_re = re.compile(r'(?:transition-duration|animation-duration)\s*:\s*(\d+)ms', re.I)
fontsize_re = re.compile(r'font-size\s*:\s*(\d+(?:\.\d+)?)px', re.I)

authored_text = "\n".join(b for _, b in authored)
px_matches = px_re.findall(authored_text)
hex_matches = hex_re.findall(authored_text)
durations = duration_re.findall(authored_text)
font_sizes = fontsize_re.findall(authored_text)
n_shadow = len(shadow_re.findall(authored_text))
n_radius = len(radius_re.findall(authored_text))

# distinct class-like selectors that are authored (custom component classes)
custom_classes = sorted({s for s, _ in authored if re.match(r'^\.[A-Za-z]', s.replace('\\',''))})

result = {
    "authored_rule_count": len(authored),
    "authored_px_values": len(px_matches),
    "authored_px_distinct": len(set(px_matches)),
    "authored_hex_values": len(hex_matches),
    "authored_hex_distinct": len(set(h.strip().lower() for h in hex_matches)),
    "authored_shadow_decls": n_shadow,
    "authored_radius_decls": n_radius,
    "authored_durations_distinct": sorted(set(int(d) for d in durations)),
    "authored_fontsize_px_distinct": sorted(set(font_sizes)),
    "custom_class_count": len(custom_classes),
    "custom_class_sample": custom_classes[:50],
}
json.dump(result, open(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\authored_metrics.json", "w"), indent=2)
print(json.dumps(result, indent=2))
