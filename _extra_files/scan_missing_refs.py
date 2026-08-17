import re, os, pathlib

refs = {
 'controllers/ai':'controllers\\ai',
 'services/configuration':'services\\configuration',
 'services/documents':'services\\documents',
 'controllers/documents':'controllers\\documents',
 'services/gateway':'services\\gateway',
 'controllers/gateway':'controllers\\gateway',
 'services/media':'services\\media',
 'services/permissions':'services\\permissions',
 'services/reporting':'services\\reporting',
 'controllers/reporting':'controllers\\reporting',
 'services/reviews':'services\\reviews',
 'controllers/reviews':'controllers\\reviews',
 'services/search':'services\\search',
 'controllers/search':'controllers\\search',
 'controllers/media':'controllers\\media',
}

hits = {k:[] for k in refs}
for root, dirs, files in os.walk('.'):
    if '__pycache__' in root or 'venv' in root or root.startswith('.\\.venv'):
        continue
    for f in files:
        if not f.endswith('.py'):
            continue
        p = os.path.join(root, f)
        try:
            txt = pathlib.Path(p).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        for k, dotted in refs.items():
            norm = dotted.replace('\\', '.')
            if re.search(r'(from\s+'+re.escape(norm)+r'\b)|(\bimport\s+'+re.escape(norm)+r'\b)', txt):
                hits[k].append(p)

for k, v in hits.items():
    print(f"{k}: {len(v)} refs")
    for x in v[:8]:
        print("   ", x)
