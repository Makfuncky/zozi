import re
import os

def parse_subrouters(filepath):
    """Parse a router file and identify sub-routers with their line ranges."""
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
    
    sub_routers = []
    for i, line in enumerate(lines):
        m = re.match(r'^_s(\d+) = APIRouter\(prefix=[\'"]([^\'"]*)[\'"]\)', line)
        if m:
            sub_routers.append({
                'num': int(m.group(1)),
                'prefix': m.group(2),
                'start_idx': i,
                'routes': []
            })
    
    for idx, sr in enumerate(sub_routers):
        end_idx = sub_routers[idx+1]['start_idx'] if idx+1 < len(sub_routers) else len(lines)
        for i in range(sr['start_idx'], end_idx):
            line = lines[i].strip()
            if re.match(r'^_s' + str(sr['num']) + r'\.(get|post|put|delete|patch)\(', line):
                m = re.search(r'\(([\'"])([^"\']+)\1', line)
                if m:
                    sr['routes'].append(m.group(2))
        sr['end_idx'] = end_idx
    
    return lines, sub_routers


def analyze_file(filepath):
    """Analyze a file and print sub-router info."""
    lines, sub_routers = parse_subrouters(filepath)
    filename = os.path.basename(filepath)
    
    print(f"\n=== {filename} ({len(lines)} lines, {len(sub_routers)} sub-routers) ===")
    
    for sr in sub_routers:
        routes_text = ', '.join(sr['routes'][:5])
        if len(sr['routes']) > 5:
            routes_text += f' ... ({len(sr["routes"])} total)'
        print(f"  _s{sr['num']:2d} prefix='{sr['prefix']}' [{len(sr['routes'])} routes]: {routes_text}")


def main():
    base = 'backend/modules/admin/routers'
    
    files = [
        'finance.py',
        'country.py',
        'governance.py',
        'catalog.py',
        'comms.py',
        'suppliers.py',
        'logistics.py',
        'orders.py',
        'security.py',
        'accounts.py',
        'customers.py',
        'hr.py',
        'promotions.py',
        'audit.py',
        'analytics.py',
    ]
    
    for filename in files:
        filepath = os.path.join(base, filename)
        if not os.path.exists(filepath):
            print(f"SKIP: {filename} not found")
            continue
        
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        if '_s0 = APIRouter(' not in content:
            print(f"SKIP: {filename} has no sub-routers")
            continue
        
        analyze_file(filepath)


if __name__ == '__main__':
    main()
