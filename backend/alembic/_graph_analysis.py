"""Temporary script to extract alembic migration graph. DELETE after use."""
import os, re

versions_dir = os.path.dirname(os.path.abspath(__file__))
files = sorted([f for f in os.listdir(versions_dir) if f.endswith('.py') and f != '_graph_analysis.py'])

corrupted_revisions = {'18afc076b757', '2f07459e835f', '48c2a8404b0e', '97126a91bc8e', 'c2d3e4f5a6b7', 'd5477adebb01', 'e3f4a5b6c7d8'}

graph = {}  # rev -> {filename, down_revision, corrupted}

# Patterns for revision and down_revision - handle type annotations
# revision: str = '...' OR revision = "..."
REV_PAT = re.compile(r"""^revision(?:\s*:\s*\w+)?\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
# down_revision: Union[...] = '...' OR down_revision = "..."
DOWN_SINGLE_PAT = re.compile(r"""^down_revision(?:\s*:\s*[^\n=]+)?\s*=\s*['"]([^'"]+)['"]""", re.MULTILINE)
# down_revision: ... = None
DOWN_NONE_PAT = re.compile(r"""^down_revision(?:\s*:\s*[^\n=]+)?\s*=\s*None""", re.MULTILINE)
# down_revision: ... = (\n  "...",\n  "...",\n)
DOWN_TUPLE_PAT = re.compile(r"""down_revision(?:\s*:\s*[^\n=]+)?\s*=\s*\(([^)]+)\)""", re.DOTALL)

for fn in files:
    fp = os.path.join(versions_dir, fn)
    with open(fp, 'rb') as f:
        raw = f.read()
    
    has_nulls = b'\x00' in raw
    content = raw.decode('utf-8', errors='replace').replace('\x00', '')
    
    rev_match = REV_PAT.search(content)
    rev = rev_match.group(1) if rev_match else None
    
    down_tuple_match = DOWN_TUPLE_PAT.search(content)
    down_single_match = DOWN_SINGLE_PAT.search(content)
    down_none_match = DOWN_NONE_PAT.search(content)
    
    if down_tuple_match:
        parts = down_tuple_match.group(1)
        downs = [s.strip().strip("'").strip('"') for s in parts.split(',') if s.strip().strip("'").strip('"')]
        down = tuple(downs)
    elif down_single_match:
        down = down_single_match.group(1)
    elif down_none_match:
        down = None
    else:
        down = '???'
    
    is_corrupted = has_nulls or (rev and rev in corrupted_revisions)
    
    graph[rev or fn] = {
        'filename': fn,
        'down_revision': down,
        'corrupted': is_corrupted
    }

# Print all entries
print("=" * 100)
print("FULL MIGRATION GRAPH")
print("=" * 100)
for rev in sorted(graph.keys()):
    info = graph[rev]
    tag = " [CORRUPTED]" if info['corrupted'] else ""
    down = info['down_revision']
    if isinstance(down, tuple):
        down_str = "(" + ", ".join(down) + ")"
    elif down is None:
        down_str = "None"
    else:
        down_str = down
    print(f"  {rev:<20s} -> down={down_str:<50s} {info['filename']}{tag}")

# Build reverse map: who points to whom
print()
print("=" * 100)
print("CHILDREN MAP (who depends on each revision)")
print("=" * 100)
children = {}  # rev -> list of children
all_revisions = set()
all_down_refs = set()

for rev, info in graph.items():
    all_revisions.add(rev)
    down = info['down_revision']
    if isinstance(down, tuple):
        for d in down:
            all_down_refs.add(d)
            children.setdefault(d, []).append(rev)
    elif down is not None and down != '???':
        all_down_refs.add(down)
        children.setdefault(down, []).append(rev)

for rev in sorted(children.keys()):
    kids = children[rev]
    tag = " [CORRUPTED]" if rev in corrupted_revisions else ""
    print(f"  {rev}{tag} is parent of: {kids}")

# Find orphans: down_revision values that don't match any known revision
print()
print("=" * 100)
print("ORPHAN ANALYSIS")
print("=" * 100)
orphan_refs = all_down_refs - all_revisions
print(f"\ndown_revision values pointing to NON-EXISTENT revisions: {orphan_refs if orphan_refs else 'NONE'}")
for ref in sorted(orphan_refs):
    kids = [rev for rev, info in graph.items() if 
            (isinstance(info['down_revision'], tuple) and ref in info['down_revision']) or
            info['down_revision'] == ref]
    print(f"  Missing revision {ref} is referenced by: {kids}")

# Find heads: revisions that nobody points to as down_revision
print()
heads = all_revisions - all_down_refs
print(f"HEAD revisions (not referenced as anyone's down_revision): {sorted(heads)}")
for h in sorted(heads):
    info = graph[h]
    tag = " [CORRUPTED]" if info['corrupted'] else ""
    print(f"  HEAD: {h} ({info['filename']}){tag}")

# Find root: revision with down_revision = None
print()
roots = [rev for rev, info in graph.items() if info['down_revision'] is None]
print(f"ROOT revisions (down_revision=None): {roots}")

# Non-corrupted files with down_revision pointing to corrupted revisions
print()
print("=" * 100)
print("NON-CORRUPTED FILES POINTING TO CORRUPTED REVISIONS")
print("=" * 100)
for rev, info in sorted(graph.items()):
    if info['corrupted']:
        continue
    down = info['down_revision']
    targets = []
    if isinstance(down, tuple):
        targets = list(down)
    elif down and down != '???':
        targets = [down]
    for t in targets:
        if t in corrupted_revisions:
            print(f"  {rev} ({info['filename']}) -> depends on CORRUPTED {t}")

# Corrupted files' listed down_revisions (may be garbled)
print()
print("=" * 100)
print("CORRUPTED FILES' EXTRACTED down_revision (may be garbled)")
print("=" * 100)
for rev, info in sorted(graph.items()):
    if info['corrupted']:
        down = info['down_revision']
        if isinstance(down, tuple):
            down_str = "(" + ", ".join(down) + ")"
        elif down is None:
            down_str = "None"
        else:
            down_str = repr(down)
        print(f"  {rev} -> down={down_str}  ({info['filename']})")

# Print complete chain analysis
print()
print("=" * 100)
print("CHAIN ANALYSIS: Walk from each head to root")
print("=" * 100)
for h in sorted(heads):
    chain = []
    current = h
    visited = set()
    while current and current != '???' and current not in visited:
        visited.add(current)
        info = graph.get(current)
        if not info:
            chain.append(f"{current} [MISSING FROM FILES]")
            break
        tag = " [CORRUPTED]" if info['corrupted'] else ""
        chain.append(f"{current}{tag}")
        down = info['down_revision']
        if isinstance(down, tuple):
            chain.append(f"  MERGE: {down}")
            break
        elif down is None:
            chain.append("  ROOT")
            break
        current = down
    print(f"\nHead: {h}")
    for c in chain:
        print(f"  -> {c}")

