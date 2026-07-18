"""Analyze alembic migration dependency graph - read-only research script."""
import os, re

versions_dir = os.path.dirname(os.path.abspath(__file__))
corrupted_revisions = {'18afc076b757','2f07459e835f','48c2a8404b0e','97126a91bc8e','c2d3e4f5a6b7','d5477adebb01','e3f4a5b6c7d8'}

graph = {}

for fn in sorted(os.listdir(versions_dir)):
    if not fn.endswith('.py') or fn.startswith('_'):
        continue
    fp = os.path.join(versions_dir, fn)
    with open(fp, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    
    has_nulls = '\x00' in content
    
    rev_match = re.search(r'^revision(?:\s*:\s*[^=]*)?\s*=\s*[\'"]([^\'"]+)[\'"]', content, re.MULTILINE)
    
    down_line_match = re.search(r'^down_revision(?:\s*:\s*[^=]*)?\s*=\s*(.*)', content, re.MULTILINE)
    
    down = 'UNPARSEABLE'
    if down_line_match:
        rhs = down_line_match.group(1).strip()
        if rhs == 'None':
            down = None
        elif rhs.startswith('('):
            parts = re.findall(r"['\"]([^'\"]+)['\"]", rhs)
            down = tuple(parts) if parts else None
        else:
            str_match = re.match(r"['\"]([^'\"]*)['\"]", rhs)
            if str_match:
                val = str_match.group(1)
                down = val if val else None
    
    fn_rev = fn.split('_')[0]
    is_corrupted = fn_rev in corrupted_revisions
    rev = rev_match.group(1) if rev_match else fn_rev
    
    graph[rev] = {
        'filename': fn,
        'down_revision': down,
        'is_corrupted': is_corrupted,
        'has_nulls': has_nulls,
    }

print("=" * 110)
print("COMPLETE MIGRATION GRAPH")
print("=" * 110)
for rev in sorted(graph.keys()):
    info = graph[rev]
    tag = " ** CORRUPTED **" if info['is_corrupted'] else ""
    null_tag = " [HAS NULLS]" if info['has_nulls'] else ""
    print(f"  {rev:<20} -> down: {str(info['down_revision']):<30} {info['filename']}{tag}{null_tag}")

all_revisions = set(graph.keys())
corrupted_set = {r for r, info in graph.items() if info['is_corrupted']}
good_set = all_revisions - corrupted_set

all_down_targets = set()
for rev, info in graph.items():
    if info['is_corrupted']:
        continue
    dr = info['down_revision']
    if dr is None or dr == 'UNPARSEABLE':
        continue
    if isinstance(dr, tuple):
        all_down_targets.update(dr)
    else:
        all_down_targets.add(dr)

print("\n" + "=" * 110)
print("ANALYSIS")
print("=" * 110)

print("\n--- NON-CORRUPTED FILES POINTING TO CORRUPTED down_revision ---")
for rev in sorted(good_set):
    info = graph[rev]
    dr = info['down_revision']
    if dr is None or dr == 'UNPARSEABLE':
        continue
    targets = list(dr) if isinstance(dr, tuple) else [dr]
    for t in targets:
        if t in corrupted_set:
            print(f"  {rev} ({info['filename']}) -> down_revision '{t}' is CORRUPTED")

print("\n--- NON-CORRUPTED FILES POINTING TO MISSING down_revision ---")
for rev in sorted(good_set):
    info = graph[rev]
    dr = info['down_revision']
    if dr is None or dr == 'UNPARSEABLE':
        continue
    targets = list(dr) if isinstance(dr, tuple) else [dr]
    for t in targets:
        if t not in all_revisions:
            print(f"  {rev} ({info['filename']}) -> down_revision '{t}' has NO FILE")

all_targets = set()
for rev, info in graph.items():
    dr = info['down_revision']
    if dr is None or dr == 'UNPARSEABLE':
        continue
    if isinstance(dr, tuple):
        all_targets.update(dr)
    else:
        all_targets.add(dr)

print("\n--- HEAD REVISIONS (no file points to them) ---")
for rev in sorted(good_set):
    if rev not in all_targets:
        info = graph[rev]
        print(f"  {rev} ({info['filename']})")

print("\n--- ROOT REVISIONS (down_revision = None) ---")
for rev in sorted(all_revisions):
    if graph[rev]['down_revision'] is None:
        print(f"  {rev} ({graph[rev]['filename']})")

print("\n--- STILL UNPARSEABLE ---")
for rev in sorted(all_revisions):
    if graph[rev]['down_revision'] == 'UNPARSEABLE':
        tag = " **CORRUPTED**" if graph[rev]['is_corrupted'] else ""
        print(f"  {rev} ({graph[rev]['filename']}){tag}")

print("\n" + "=" * 110)
print("CORRUPTED FILE DEPENDENCY ANALYSIS")
print("=" * 110)
for crev in sorted(corrupted_set):
    info = graph[crev]
    print(f"\n  CORRUPTED: {crev} ({info['filename']})")
    children = []
    for rev, rinfo in graph.items():
        dr = rinfo['down_revision']
        if dr is None or dr == 'UNPARSEABLE':
            continue
        targets = list(dr) if isinstance(dr, tuple) else [dr]
        if crev in targets:
            tag = " (CORRUPTED)" if rinfo['is_corrupted'] else ""
            children.append(f"{rev}{tag}")
    print(f"    Children (point to this): {children}")
    print(f"    Own down_revision: {info['down_revision']}")

print("\n" + "=" * 110)
print("FULL DEPENDENCY TREE")
print("=" * 110)

children_map = {}
for rev, info in graph.items():
    dr = info['down_revision']
    if dr is None or dr == 'UNPARSEABLE':
        continue
    targets = list(dr) if isinstance(dr, tuple) else [dr]
    for t in targets:
        children_map.setdefault(t, []).append(rev)

roots = [r for r, info in graph.items() if info['down_revision'] is None]
visited = set()

def walk(rev, depth=0):
    if rev in visited:
        return
    visited.add(rev)
    info = graph.get(rev, {})
    tag = " **CORRUPTED**" if info.get('is_corrupted') else ""
    fn = info.get('filename', 'MISSING')
    print(f"{'  ' * (depth+1)}{rev} ({fn}){tag}")
    for child in sorted(children_map.get(rev, [])):
        walk(child, depth + 1)

for root in sorted(roots):
    walk(root)

unvisited = all_revisions - visited
if unvisited:
    print(f"\n  DISCONNECTED ({len(unvisited)} revisions):")
    for rev in sorted(unvisited):
        tag = " **CORRUPTED**" if graph[rev]['is_corrupted'] else ""
        print(f"    {rev} ({graph[rev]['filename']}){tag} down={graph[rev]['down_revision']}")

