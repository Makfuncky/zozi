import tinycss2, json, os

GLOBALS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\styles\globals.css"
REGEN  = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\regen.css"
OUT    = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\split.json"

def norm_decl(decls):
    # decls: list of (name_lower, value_normalized)
    return tuple(sorted((n, v) for n, v in decls))

def parse_rules(path):
    text = open(path, encoding="utf-8").read()
    tokens = tinycss2.parse_stylesheet(text, skip_whitespace=True)
    rules = []
    atrules = 0
    for t in tokens:
        if t.type == "at-rule":
            atrules += 1
            # descend into at-rule blocks (media, supports, layer)
            if t.content:
                for c in tinycss2.parse_rule_list(t.content, skip_whitespace=True):
                    if c.type == "qualified-rule":
                        sel = " ".join(t2.serialize() for t2 in c.prelude).strip()
                        decls = [(d.lower_name, " ".join(x.serialize() for x in d.value).strip())
                                 for d in c.content if d.type == "declaration" and not d.lower_name.startswith("--")]
                        rules.append((sel, norm_decl(decls)))
        elif t.type == "qualified-rule":
            sel = " ".join(t2.serialize() for t2 in t.prelude).strip()
            decls = [(d.lower_name, " ".join(x.serialize() for x in d.value).strip())
                     for d in t.content if d.type == "declaration" and not d.lower_name.startswith("--")]
            rules.append((sel, norm_decl(decls)))
    return rules, atrules

g_rules, g_at = parse_rules(GLOBALS)
r_rules, r_at = parse_rules(REGEN)

# index regen by (selector, decl)
regen_index = {}
for sel, decl in r_rules:
    regen_index.setdefault(sel, set()).add(decl)

matched = 0          # rules in globals that EXACTLY match a regen rule -> deletable
matched_decls_kinds = {}
hand_authored = []   # (selector, num_decls)
for sel, decl in g_rules:
    if sel in regen_index and decl in regen_index[sel]:
        matched += 1
    else:
        hand_authored.append((sel, len(decl)))

# categorize hand-authored selectors
import re
def kind(sel):
    if sel.startswith("@") or sel.startswith(":"):
        return "pseudo/global"
    if re.match(r'^[.#]?[a-zA-Z][\w-]*$', sel) and " " not in sel and ":" not in sel and "[" not in sel:
        # single compound class/id/tag
        if re.match(r'^\.[a-z][a-z0-9-]*$', sel):
            return "custom-component-class"
        return "tag-or-id"
    return "complex-selector"

from collections import Counter
kinds = Counter(kind(s) for s, _ in hand_authored)

result = {
    "globals_lines": sum(1 for _ in open(GLOBALS, encoding="utf-8")),
    "globals_top_rules": len(g_rules),
    "globals_atrules": g_at,
    "regen_top_rules": len(r_rules),
    "regen_atrules": r_at,
    "matched_deletable": matched,
    "hand_authored_count": len(hand_authored),
    "hand_authored_kinds": dict(kinds),
    "hand_authored_sample": [s for s, _ in hand_authored[:60]],
}
json.dump(result, open(OUT, "w"), indent=2)
print(json.dumps(result, indent=2))
