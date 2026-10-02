#!/usr/bin/env python3
"""Split file index into smaller batches for parallel agent investigation."""
import json
from pathlib import Path

with open("_audit/compiler/file_index.json", "r", encoding="utf-8") as f:
    file_index = json.load(f)

# Phase ordering
phase_order = {
    "emergency": 0, "boot": 1, "tech": 2, "db": 3, "logic": 4,
    "arch": 5, "security": 6, "frontend": 7, "mobile": 7,
    "testing": 8, "infra": 9, "defer": 10, "compliance": 8
}

# Group files by phase
files_by_phase = []
for file_path, findings in file_index.items():
    phases = [f.get("Phase", "defer") for f in findings]
    earliest = min(phases, key=lambda p: phase_order.get(p, 99))
    files_by_phase.append((earliest, file_path, findings))

# Sort by phase
files_by_phase.sort(key=lambda x: (phase_order.get(x[0], 99), x[1]))

# Create batches of 3 files each
batches = []
batch_size = 3
for i in range(0, len(files_by_phase), batch_size):
    batch = files_by_phase[i:i+batch_size]
    batches.append(batch)

print(f"Total files: {len(files_by_phase)}")
print(f"Total batches (agents): {len(batches)}")
for i, batch in enumerate(batches[:5]):
    print(f"Batch {i+1}: {[b[1] for b in batch]}")
print("...")
for i, batch in enumerate(batches[-3:]):
    print(f"Batch {len(batches)-2+i}: {[b[1] for b in batch]}")

# Write batches
with open("_audit/compiler/batches_small.json", "w", encoding="utf-8") as f:
    json.dump(batches, f, indent=2, ensure_ascii=False)
