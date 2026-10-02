#!/usr/bin/env python3
"""Write compiler checkpoint.json."""
import json
from pathlib import Path
from collections import defaultdict

AUDIT_DIR = Path("_audit")
COMPILER_DIR = AUDIT_DIR / "compiler"

with open(COMPILER_DIR / "aggregated_results.json", "r", encoding="utf-8") as f:
    findings = json.load(f)

status_counts = defaultdict(int)
for fid, data in findings.items():
    status_counts[data["status"]] += 1

checkpoint = {
    "status": "COMPLETE",
    "total_batches": 57,
    "total_findings": len(findings),
    "status_counts": dict(status_counts),
    "batches_completed": list(range(1, 58)),
    "output_files": [
        str(COMPILER_DIR / "aggregated_results.json"),
        str(AUDIT_DIR / "TO_BE_RESOLVE.md"),
        str(COMPILER_DIR / "COMPILER_LOG.md"),
        str(COMPILER_DIR / "checkpoint.json"),
    ]
}

with open(COMPILER_DIR / "checkpoint.json", "w", encoding="utf-8") as f:
    json.dump(checkpoint, f, indent=2, ensure_ascii=False)

print("Checkpoint written to compiler/checkpoint.json")
print(json.dumps(checkpoint, indent=2))
