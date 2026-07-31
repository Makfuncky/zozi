import json
from collections import Counter

with open('.governance/architecture_registry.json', 'r') as f:
    reg = json.load(f)

illegal = reg.get('illegal_edges', [])
print(f'Total illegal edges: {len(illegal)}')
print()

# Group by reason
reasons = Counter()
for e in illegal:
    reasons[e.get('illegal_reason', '?')] += 1

print("By reason:")
for reason, count in reasons.most_common():
    print(f"  {count:3d}  {reason}")

print()
print("All illegal edges:")
for e in sorted(illegal, key=lambda x: x.get('caller', '') + x.get('callee', '')):
    caller = e.get('caller', '?')
    callee = e.get('callee', '?')
    reason = e.get('illegal_reason', '')
    print(f"  {caller:50s} -> {callee:50s} : {reason}")
