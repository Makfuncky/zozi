#!/usr/bin/env python3
"""Build file index from all dimension files for the compiler."""
import json
import re
from pathlib import Path
from collections import defaultdict

AUDIT_DIR = Path("_audit")
DIMS_DIR = AUDIT_DIR / "dimensions"

def parse_findings(filepath):
    """Parse findings table from a dimension markdown file."""
    findings = []
    with open(filepath, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    
    lines = content.split("\n")
    in_table = False
    header = None
    
    for line in lines:
        line = line.strip()
        if not line.startswith("|"):
            in_table = False
            continue
        
        if "ID" in line and "Phase" in line and "Status" in line:
            in_table = True
            header = [c.strip() for c in line.split("|")[1:-1]]
            continue
        
        if in_table and line.startswith("|----"):
            continue
        
        if in_table and header:
            cols = [c.strip() for c in line.split("|")[1:-1]]
            if len(cols) == len(header):
                finding = dict(zip(header, cols))
                finding["_source"] = filepath.name
                findings.append(finding)
    
    return findings

all_findings = []
for f in sorted(DIMS_DIR.glob("*.md")):
    if f.name.startswith("."):
        continue
    findings = parse_findings(f)
    all_findings.extend(findings)

print(f"Total findings parsed: {len(all_findings)}")

# Group by file
file_index = defaultdict(list)
for f in all_findings:
    file_path = f.get("File:Line", "").split(":")[0]
    if file_path:
        file_index[file_path].append(f)

print(f"Unique files: {len(file_index)}")

# Write file index
with open("_audit/compiler/file_index.json", "w", encoding="utf-8") as out:
    json.dump(dict(file_index), out, indent=2, ensure_ascii=False)

# Print summary
for file_path in sorted(file_index.keys())[:20]:
    findings = file_index[file_path]
    phases = [f.get("Phase", "") for f in findings]
    earliest_phase = min(phases, key=lambda p: ["emergency","boot","tech","db","logic","arch","security","frontend","defer"].index(p) if p in ["emergency","boot","tech","db","logic","arch","security","frontend","defer"] else 99)
    print(f"{file_path}: {len(findings)} findings, phase={earliest_phase}")
