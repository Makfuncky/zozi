#!/usr/bin/env python3
"""Update dimension file statuses based on aggregated findings."""
import json
import re
from pathlib import Path

AUDIT_DIR = Path("_audit")
DIMENSIONS_DIR = AUDIT_DIR / "dimensions"
COMPILER_DIR = AUDIT_DIR / "compiler"

with open(COMPILER_DIR / "aggregated_results.json", "r", encoding="utf-8") as f:
    findings = json.load(f)

# Find all dimension markdown files
dim_files = list(DIMENSIONS_DIR.glob("*.md"))
print(f"Found {len(dim_files)} dimension files")

updated_count = 0
skipped = []

for dim_file in dim_files:
    try:
        with open(dim_file, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(dim_file, "r", encoding="cp1252") as f:
                content = f.read()
        except Exception as e:
            skipped.append((dim_file.name, str(e)))
            continue
    
    # Find all findings in this dimension file and update their status
    # Pattern: | FINDING-ID | phase | STATUS | ...
    def replace_status(match):
        finding_id = match.group(1)
        # Check if this finding is in our aggregated results
        if finding_id in findings:
            new_status = findings[finding_id]["status"]
            # Replace the status in the table row (3rd field)
            return match.group(0).replace("| NEW |", f"| {new_status} |", 1)
        return match.group(0)
    
    # Apply replacement - match | ID | ... | NEW | pattern
    new_content = re.sub(r'\| ([A-Z]+-\d+) \| [^|]+ \| NEW \|', replace_status, content)
    
    if new_content != content:
        with open(dim_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        updated_count += 1
        print(f"  Updated {dim_file.name}")

if skipped:
    print(f"Skipped {len(skipped)} files: {skipped}")

print(f"Updated {updated_count} dimension files with compiled statuses")
