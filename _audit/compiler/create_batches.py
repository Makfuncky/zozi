#!/usr/bin/env python3
"""Split file index into batches for parallel agent investigation."""
import json
from pathlib import Path
from collections import defaultdict

with open("_audit/compiler/file_index.json", "r", encoding="utf-8") as f:
    file_index = json.load(f)

# Phase ordering
phase_order = {
    "emergency": 0, "boot": 1, "tech": 2, "db": 3, "logic": 4,
    "arch": 5, "security": 6, "frontend": 7, "mobile": 7,
    "testing": 8, "infra": 9, "defer": 10, "compliance": 8
}

# Group files by phase
files_by_phase = defaultdict(list)
for file_path, findings in file_index.items():
    phases = [f.get("Phase", "defer") for f in findings]
    earliest = min(phases, key=lambda p: phase_order.get(p, 99))
    files_by_phase[earliest].append(file_path)

# Create batches of ~10 files each
batches = []
batch_size = 10
all_files = []
for phase in ["emergency", "boot", "tech", "db", "logic", "arch", "security", "frontend", "mobile", "testing", "infra", "defer"]:
    all_files.extend(files_by_phase.get(phase, []))

for i in range(0, len(all_files), batch_size):
    batch = all_files[i:i+batch_size]
    batches.append(batch)

print(f"Total files: {len(all_files)}")
print(f"Total batches: {len(batches)}")
for i, batch in enumerate(batches):
    print(f"Batch {i+1}: {len(batch)} files")

# Write batches
with open("_audit/compiler/batches.json", "w", encoding="utf-8") as f:
    json.dump(batches, f, indent=2)
