#!/usr/bin/env python3
"""Generate _audit/TO_BE_RESOLVE.md from aggregated results."""
import json
from pathlib import Path
from collections import defaultdict

AUDIT_DIR = Path("_audit")
COMPILER_DIR = AUDIT_DIR / "compiler"

with open(COMPILER_DIR / "aggregated_results.json", "r", encoding="utf-8") as f:
    findings = json.load(f)

# Group by file
by_file = defaultdict(list)
for fid, data in findings.items():
    by_file[data["file"]].append({
        "id": fid,
        "status": data["status"],
        "evidence": data["evidence"],
        "counter_evidence": data["counter_evidence"],
        "benchmark_mismatch": data["benchmark_mismatch"],
        "notes": data["notes"],
    })

# Sort files alphabetically
sorted_files = sorted(by_file.keys())

lines = [
    "# TO_BE_RESOLVE.md",
    "",
    "## Compiled Forensic Audit Findings",
    "",
    f"Total findings: {len(findings)}",
    f"- VALID: {sum(1 for f in findings.values() if f['status'] == 'VALID')}",
    f"- INVALID: {sum(1 for f in findings.values() if f['status'] == 'INVALID')}",
    f"- RESOLVED: {sum(1 for f in findings.values() if f['status'] == 'RESOLVED')}",
    f"- BENCHMARK_MISMATCH: {sum(1 for f in findings.values() if f['status'] == 'BENCHMARK_MISMATCH')}",
    f"- PARTIALLY_VALID: {sum(1 for f in findings.values() if f['status'] == 'PARTIALLY_VALID')}",
    "",
    "---",
    ""
]

for file_path in sorted_files:
    file_findings = by_file[file_path]
    lines.append(f"## {file_path}")
    lines.append("")
    
    valid_findings = [f for f in file_findings if f["status"] == "VALID"]
    invalid_findings = [f for f in file_findings if f["status"] == "INVALID"]
    resolved_findings = [f for f in file_findings if f["status"] == "RESOLVED"]
    bm_findings = [f for f in file_findings if f["status"] == "BENCHMARK_MISMATCH"]
    pv_findings = [f for f in file_findings if f["status"] == "PARTIALLY_VALID"]
    
    lines.append(f"**Status:** {len(valid_findings)} VALID, {len(invalid_findings)} INVALID, {len(resolved_findings)} RESOLVED, {len(bm_findings)} BENCHMARK_MISMATCH, {len(pv_findings)} PARTIALLY_VALID")
    lines.append("")
    
    if valid_findings:
        lines.append("### VALID Findings")
        lines.append("")
        for f in valid_findings:
            lines.append(f"- **{f['id']}**: {f['evidence']}")
            if f.get("benchmark_mismatch"):
                lines.append(f"  - Benchmark mismatch: {f['benchmark_mismatch']}")
        lines.append("")
    
    if pv_findings:
        lines.append("### PARTIALLY_VALID Findings")
        lines.append("")
        for f in pv_findings:
            lines.append(f"- **{f['id']}**: {f['evidence']}")
        lines.append("")
    
    if bm_findings:
        lines.append("### BENCHMARK_MISMATCH Findings")
        lines.append("")
        for f in bm_findings:
            lines.append(f"- **{f['id']}**: {f['evidence']}")
            lines.append(f"  - Mismatch: {f['benchmark_mismatch']}")
        lines.append("")
    
    if resolved_findings:
        lines.append("### RESOLVED Findings")
        lines.append("")
        for f in resolved_findings:
            lines.append(f"- **{f['id']}**: {f['counter_evidence'] or 'Already fixed in source'}")
        lines.append("")
    
    if invalid_findings:
        lines.append("### INVALID Findings")
        lines.append("")
        for f in invalid_findings:
            lines.append(f"- **{f['id']}**: {f['counter_evidence'] or 'False positive'}")
        lines.append("")
    
    lines.append("---")
    lines.append("")

with open(AUDIT_DIR / "TO_BE_RESOLVE.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Generated {AUDIT_DIR / 'TO_BE_RESOLVE.md'}")
