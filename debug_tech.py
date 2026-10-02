import re
from pathlib import Path

content = Path('frontend/web_app/package.json').read_text(encoding='utf-8', errors='ignore')
ts = re.search(r'"typescript"\s*:\s*"[^"]*5\.9\.3[^"]*"', content)
print('match:', ts.group(0) if ts else 'NONE')
print('has 5.9.3 anywhere:', '5.9.3' in content)
