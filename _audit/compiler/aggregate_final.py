#!/usr/bin/env python3
"""Aggregate all 57 batch results and produce final compiler outputs."""
import json
from pathlib import Path
from collections import defaultdict

AUDIT_DIR = Path("_audit")
COMPILER_DIR = AUDIT_DIR / "compiler"

# Load all batch results by filename
all_results = {}
for batch_file in sorted(COMPILER_DIR.glob("results_batch_*.json")):
    with open(batch_file, "r", encoding="utf-8") as f:
        batch_data = json.load(f)
        all_results[batch_file.name] = batch_data

print(f"Loaded {len(all_results)} batch result files")

# Aggregate by finding ID
finding_status = {}
for filename, batch in all_results.items():
    batch_num = batch.get("batch", "?")
    for file_data in batch.get("files", []):
        file_path = file_data.get("path", "")
        for finding in file_data.get("findings", []):
            fid = finding.get("id", "")
            finding_status[fid] = {
                "status": finding.get("status", "VALID"),
                "file": file_path,
                "batch": batch_num,
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

# Write COMPILER_LOG.md
log_lines = [
    "# Forensic Audit Compiler Log",
    "",
    "## Run Summary",
    f"- Total batches: {len(all_results)}",
    f"- Total findings re-verified: {len(finding_status)}",
    f"- VALID: {status_counts.get('VALID', 0)}",
    f"- INVALID: {status_counts.get('INVALID', 0)}",
    f"- RESOLVED: {status_counts.get('RESOLVED', 0)}",
    f"- BENCHMARK_MISMATCH: {status_counts.get('BENCHMARK_MISMATCH', 0)}",
    "",
    "## Batch Details",
    ""
]

for filename in sorted(all_results.keys()):
    batch = all_results[filename]
    batch_num = batch.get("batch", "?")
    files = batch.get("files", [])
    file_count = len(files)
    finding_count = sum(len(f.get("findings", [])) for f in files)
    log_lines.append(f"- {filename}: batch={batch_num}, files={file_count}, findings={finding_count}")

log_lines.extend([
    "",
    "## Generated Files",
    f"- `{COMPILER_DIR / 'aggregated_results.json'}`",
    f"- `{AUDIT_DIR / 'TO_BE_RESOLVE.md'}` (pending generation)",
    ""
])

with open(COMPILER_DIR / "COMPILER_LOG.md", "w", encoding="utf-8") as f:
    f.write("\n".join(log_lines))

print("Compiler log written to compiler/COMPILER_LOG.md")
