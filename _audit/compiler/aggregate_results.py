#!/usr/bin/env python3
"""Aggregate all batch results and produce final compiler outputs."""
import json
from pathlib import Path
from collections import defaultdict

AUDIT_DIR = Path("_audit")
COMPILER_DIR = AUDIT_DIR / "compiler"

# Load all batch results
all_results = {}
for i in range(1, 17):
    batch_file = COMPILER_DIR / f"results_batch_{i}.json"
    if batch_file.exists():
        with open(batch_file, "r", encoding="utf-8") as f:
            batch_data = json.load(f)
            all_results[batch_data["batch"]] = batch_data

print(f"Loaded {len(all_results)} batch results")

# Aggregate by finding ID
finding_status = {}
for batch_num, batch in all_results.items():
    for file_data in batch.get("files", []):
        file_path = file_data.get("path", "")
        for finding in file_data.get("findings", []):
            fid = finding.get("id", "")
            finding_status[fid] = {
                "status": finding.get("status", "VALID"),
                "file": file_path,
                "evidence": finding.get("evidence", ""),
                "counter_evidence": finding.get("counter_evidence", ""),
                "benchmark_mismatch": finding.get("benchmark_mismatch", ""),
                "notes": finding.get("notes", ""),
            }

print(f"Total findings re-verified: {len(finding_status)}")

# Count statuses
status_counts = defaultdict(int)
for fid, data in finding_status.items():
    status_counts[data["status"]] += 1

print("Status counts:")
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

# Write aggregated results
with open(COMPILER_DIR / "aggregated_results.json", "w", encoding="utf-8") as f:
    json.dump(finding_status, f, indent=2, ensure_ascii=False)

print("Aggregated results written to compiler/aggregated_results.json")
