"""Classify SYM2 (duplicate-symbol) audit findings.

The audit flags ANY class / public function name defined in >1 module. Many of
these are intentional architectural patterns in this generated monolith:
  - TEST FIXTURE : any module under tests/ (pytest fixtures like admin_headers)
  - VERSIONED    : duplicate name across router version files (api_x_routes / _2 / _3)
  - LAYER MIRROR : same operation name in router + controller + service (by design)
  - HELPER COPY  : small DB/write helpers copied into many write_*_service modules
  - GENUINE      : same concept implemented in 2+ places with no layering rationale

We categorize each finding and report counts; genuine ones are candidates to fix.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(r"D:\Projects\10- E-COMMERCE WEBSITE\zozi")
REPORT = REPO / "ARCHITECTURE_AUDIT_REPORT.md"
OUT = REPO / "_extra_files" / "sym2_classification.json"

# module lists look like: `a.b:15, a.c:20`
ENTRY_RE = re.compile(r"`([^`]+)`")
LINE_RE = re.compile(r"SYM2\s*\|\s*backend\s*\|\s*`([^`]+)`\s*\|\s*(class|public function) '([^']+)' defined in (\d+) modules")


def categorize(modules: list[str], name: str) -> str:
    mods = [m.split(":")[0] for m in modules]
    # test fixture duplication
    if any(m.startswith("tests.") for m in mods):
        return "TEST_FIXTURE"
    # versioned router duplication (api_foo_routes / _2 / _3)
    bases = {m.rsplit("_", 1)[0] if re.search(r"_\d+$", m) else m for m in mods}
    if len(mods) >= 2 and any(re.search(r"_\d+$", m) for m in mods) and len(bases) < len(mods):
        return "VERSIONED_ROUTER"
    # layer mirroring: at least one router/controllers AND one services
    layers = {m.split(".")[0] for m in mods}
    if {"routers", "controllers"} & layers and "services" in layers:
        return "LAYER_MIRROR"
    if {"routers", "controllers"} & layers and len(layers) >= 2:
        return "LAYER_MIRROR"
    # helper copies: write_helpers / *_write_service / *_read_service
    if any(("write_service" in m or "read_service" in m or m.endswith("write_helpers")) for m in mods):
        return "HELPER_COPY"
    return "GENUINE"


def main() -> None:
    text = REPORT.read_text(encoding="utf-8", errors="replace")
    results = []
    for m in LINE_RE.finditer(text):
        loc, kind, name, nmods = m.groups()
        modules = [x.strip() for x in loc.split(",")]
        cat = categorize(modules, name)
        results.append(
            {
                "name": name,
                "kind": kind,
                "count": int(nmods),
                "modules": modules,
                "category": cat,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, indent=2), encoding="utf-8")
    from collections import Counter
    c = Counter(r["category"] for r in results)
    print(f"SYM2 entries parsed : {len(results)}")
    for k, v in c.most_common():
        print(f"  {k:16s}: {v}")
    print("\nGENUINE duplicates:")
    for r in results:
        if r["category"] == "GENUINE":
            print(f"  - {r['name']} ({r['kind']}) x{r['count']}: {', '.join(r['modules'])}")
    print(f"\nClassification written to {OUT}")


if __name__ == "__main__":
    main()
