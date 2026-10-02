from pathlib import Path
import re

content = Path('_audit/dimensions/03_logical.md').read_text(encoding='utf-8')
lines = content.splitlines()

# Extract all file references from FIND-03-xxx and L-NEW-xxx findings
findings = []
current_id = None
current_files = []
current_evidence = []

for line in lines:
    if '#### FIND-03-' in line or '### L-NEW-' in line:
        if current_id:
            findings.append((current_id, current_files, current_evidence))
        m = re.search(r'(FIND-03-\d+|L-NEW-\d+)', line)
        current_id = m.group(1) if m else None
        current_files = []
        current_evidence = []
    elif current_id:
        # Match file:line patterns like `backend/.../file.py:80-84` or `backend/.../file.py:59,70`
        file_matches = re.findall(r'`([^`]+\.py:\d+[^`]*)`', line)
        current_files.extend(file_matches)
        # Also capture code evidence
        if line.strip().startswith('```'):
            continue
        current_evidence.append(line.strip())

if current_id:
    findings.append((current_id, current_files, current_evidence))

with open('debug_new_findings.txt', 'w', encoding='utf-8') as f:
    for fid, files, evidence in findings:
        f.write(f"{fid}:\n")
        for file_ref in files:
            f.write(f"  {file_ref}\n")
        f.write('\n')
