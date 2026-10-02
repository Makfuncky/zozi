from pathlib import Path

content = Path('_audit/dimensions/03_logical.md').read_text(encoding='utf-8')
lines = content.splitlines()
findings = [l for l in lines if '### L-NEW-' in l or '#### FIND-03-' in l]
with open('debug_logical_out.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total findings: {len(findings)}\n")
    for i, finding in enumerate(findings, 1):
        f.write(f"{i}: {finding}\n")
