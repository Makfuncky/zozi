import sys
sys.path.insert(0, 'scripts/system_trackers')
from feature_tracker import *
import traceback
import argparse
from collections import Counter

try:
    ap = argparse.ArgumentParser()
    ap.add_argument('--no-ollama', action='store_true')
    ap.add_argument('--feature', default=None)
    ap.add_argument('--output', default=str(ROOT / 'documents' / 'FEATURE_TRACKER.md'))
    ap.add_argument('--json-out', default=str(ROOT / 'documents' / 'FEATURE_TRACKER.json'))
    args = ap.parse_args(['--no-ollama'])
    ollama = OllamaClient(enabled=not args.no_ollama)
    repo = Repo(ROOT)
    reg = Registry(repo)
    defs_path = ROOT / 'scripts' / 'system_trackers' / 'feature_definitions.yaml'
    defs = yaml.safe_load(defs_path.read_text(encoding='utf-8'))
    feats = defs.get('features') or []
    results = []
    for feat in feats:
        spec = parse_feature_spec(feat)
        result = verify_feature(repo, reg, spec, ollama)
        results.append(result)
    discovered = discover_features_from_codebase(repo)
    print(f'Discovered {len(discovered)} features')
    c = Counter(d['spec']['section'] for d in discovered)
    print('By section:', dict(c))
    for d in discovered[:30]:
        print(f"  {d['spec']['section']} {d['spec']['name']}: {len(d['matched'])} files, {d['scores']['overall']}%")
except Exception as e:
    traceback.print_exc()
