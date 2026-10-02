import json
from pathlib import Path

p = Path(r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\_audit\verification_results.json')
data = json.loads(p.read_text())

arch = data['dimensions']['01_architectural']['verified']
for r in arch:
    if r['id'] in ['ARCH-015', 'ARCH-018', 'ARCH-019', 'ARCH-025', 'ARCH-041', 'ARCH-042']:
        print(f"{r['id']}: {r['status']} - {r['evidence'][:100]}")
