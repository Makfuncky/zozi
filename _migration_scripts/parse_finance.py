import re

with open('backend/modules/admin/routers/finance.py', 'r') as f:
    lines = f.readlines()

# Find sub-router definitions
sub_routers = []
for i, line in enumerate(lines):
    m = re.match(r'^_s(\d+) = APIRouter\(prefix=[\'"]([^\'"]*)[\'"]\)', line)
    if m:
        sub_routers.append({
            'num': int(m.group(1)),
            'prefix': m.group(2),
            'start_line': i + 1,
            'routes': []
        })

# For each sub-router, find the routes registered to it
for idx, sr in enumerate(sub_routers):
    end_line = sub_routers[idx+1]['start_line'] if idx+1 < len(sub_routers) else len(lines)
    # Find all route registrations for this sub-router
    for i in range(sr['start_line']-1, end_line):
        line = lines[i].strip()
        if re.match(r'^_s' + str(sr['num']) + r'\.(get|post|put|delete|patch)\(', line):
            # Extract the route path
            m = re.search(r'\(([\'"])([^"\']+)\1', line)
            if m:
                sr['routes'].append(m.group(2))

# Print summary
for sr in sub_routers:
    routes_preview = ', '.join(sr['routes'][:3])
    print(f"_s{sr['num']} (prefix='{sr['prefix']}') - {len(sr['routes'])} routes: [{routes_preview}...]")
