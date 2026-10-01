import tinycss2, json, re
from collections import Counter, OrderedDict

GLOBALS = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\src\styles\globals.css"
OUT    = r"D:\Projects\10- E-COMMERCE WEBSITE\zozi\frontend\web_app\_extra_files\gcss_proto\split.json"

# Tailwind utility-shaped selector prefixes (the tell-tale tokens)
UTIL_PREFIX = re.compile(
    r'^(?:\\?)?(?:'
    r'\!?(?:container|sr-only|not-sr-only|pointer-events|visible|invisible|static|fixed|absolute|relative|sticky|'
    r'inset|top|right|bottom|left|z|flex|inline-flex|grid|block|inline-block|inline|flow-root|contents|list-item|'
    r'hidden|w-|min-w|max-w|h-|min-h|max-h|'
    r'px-|py-|pt-|pr-|pb-|pl-|mx-|my-|mt-|mr-|mb-|ml-|'
    r'font|text-|bg-|border|rounded|shadow|ring|outline|opacity|'
    r'cursor|select|resize|appearance|pointer|touch|user|will-change|'
    r'overflow|overscroll|object|object-cover|'
    r'table|align|'
    r'p-|m-|gap-|space-|divide|'
    r'transition|duration|ease|delay|animate|'
    r'scale|rotate|translate|skew|transform|origin|'
    r'content-|items-|self-|justify-|place-|'
    r'fill|stroke|stroke-width|antialiased|italic|uppercase|lowercase|capitalize|underline|line-through|'
    r'tracking|leading|list-|decoration|whitespace|break|truncate|'
    r'aspect|columns|columns-|col-|row-|'
    r'blur|backdrop|'
    r'float|clear|'
    r'odd|even|first|last|only|empty|disabled|enabled|checked|focus|hover|active|visited|'
    r')'
    r')'
)

# Known hand-authored (custom) class names observed
CUSTOM_KNOWN = {
    '.glass-dropdown', '.glass-search', '.theme-card', '.sr-only', '.container',
}

def sel_shape(sel):
    """Return 'utility' if selector looks like a Tailwind utility, else 'custom'."""
    s = sel.strip()
    # strip escaped backslashes for inspection
    base = s.replace('\\', '')
    # pseudo-state prefixes like hover:, focus: attached
    # take the last compound (after last space or combinator) for class check
    parts = re.split(r'(?<!\\)[\s>+~]', base)
    last = parts[-1]
    # remove state variant prefixes (hover:, md:, etc.)
    last = re.sub(r'^[a-z]+:', '', last)
    if UTIL_PREFIX.match(last):
        return 'utility'
    # custom component class heuristics
    if re.match(r'^\.[A-Za-z][\w-]*$', last):
        return 'custom-class'
    if re.match(r'^[a-z][a-z-]*$', last) and ':' not in last:
        return 'tag'  # bare element selector -> base layer, keep
    return 'other'

def decls_of(content):
    return [(d.lower_name, " ".join(x.serialize() for x in d.value).strip())
            for d in content if d.type == "declaration" and not d.lower_name.startswith("--")]

def parse(path):
    text = open(path, encoding="utf-8").read()
    toks = tinycss2.parse_stylesheet(text, skip_whitespace=True)
    out = []  # list of dicts: type, name/selector, shape, n_decls, raw_prelude
    for t in toks:
        if t.type == "at-rule":
            name = t.lower_at_keyword
            pre = " ".join(x.serialize() for x in t.prelude).strip()
            if name in ("media", "supports", "layer") and t.content:
                inner = tinycss2.parse_rule_list(t.content, skip_whitespace=True)
                shapes = []
                n_rules = 0
                for c in inner:
                    if c.type == "qualified-rule":
                        sel = " ".join(x.serialize() for x in c.prelude).strip()
                        sh = sel_shape(sel)
                        shapes.append(sh)
                        n_rules += 1
                dom = Counter(shapes).most_common(1)[0][0] if shapes else "other"
                out.append({"type": "at-" + name, "prelude": pre, "shape": dom,
                            "n_inner": n_rules, "inner_shapes": dict(Counter(shapes))})
            else:
                out.append({"type": "at-" + name, "prelude": pre, "shape": "at-other", "n_inner": 0})
        elif t.type == "qualified-rule":
            sel = " ".join(x.serialize() for x in t.prelude).strip()
            out.append({"type": "rule", "selector": sel, "shape": sel_shape(sel),
                        "n_decls": len(decls_of(t.content))})
    return out

g = parse(GLOBALS)

shape_counter = Counter()
rule_shapes = Counter()
at_shape_counter = Counter()
at_media_util = 0
at_media_custom = 0
at_media_mixed = 0
keep_examples = []
drop_examples = []

for item in g:
    if item["type"] == "rule":
        rule_shapes[item["shape"]] += 1
        if item["shape"] in ("utility",):
            drop_examples.append(item["selector"])
        else:
            keep_examples.append((item["shape"], item["selector"]))
    elif item["type"].startswith("at-"):
        shape_counter[item["shape"]] += 1
        if item["type"] == "at-media":
            ish = item["inner_shapes"]
            if ish.get("utility", 0) and ish.get("utility") == item["n_inner"]:
                at_media_util += 1
            elif ish.get("utility", 0) == 0:
                at_media_custom += 1
            else:
                at_media_mixed += 1
        elif item["type"] == "at-layer":
            at_shape_counter[item["shape"]] += 1

result = {
    "globals_lines": sum(1 for _ in open(GLOBALS, encoding="utf-8")),
    "total_top_items": len(g),
    "top_level_rule_shapes": dict(rule_shapes),
    "top_level_atrule_shapes": dict(shape_counter),
    "at_media_breakdown": {"all-utility": at_media_util, "all-custom": at_media_custom, "mixed": at_media_mixed},
    "at_layer_shapes": dict(at_shape_counter),
    "keep_sample": keep_examples[:50],
    "drop_sample": drop_examples[:40],
}
json.dump(result, open(OUT, "w"), indent=2)
print(json.dumps(result, indent=2))
