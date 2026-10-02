from pathlib import Path
import re

content = Path('_audit/dimensions/03_logical.md').read_text(encoding='utf-8')
lines = content.splitlines()

# Extract FIND-03-xxx findings
find_03 = []
i = 0
while i < len(lines):
    if '#### FIND-03-' in lines[i]:
        header = lines[i]
        m = re.match(r'#### (FIND-03-\d+):', header)
        fid = m.group(1) if m else f'FIND-03-{i}'
        # Find the Files: section
        file_lines = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith('####') and not lines[j].startswith('###'):
            if 'Files:' in lines[j] or 'File:' in lines[j] or '```' in lines[j]:
                file_lines.append(lines[j])
            j += 1
        find_03.append((fid, header, file_lines))
    i += 1

with open('debug_findings.txt', 'w', encoding='utf-8') as f:
    for fid, header, file_lines in find_03:
        f.write(f"{fid}: {header}\n")
        for fl in file_lines:
            f.write(f"  {fl}\n")
        f.write('\n')
