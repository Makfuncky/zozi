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


def get_import_block(lines):
    """Extract the import block (everything before the first sub-router definition)."""
    end_idx = len(lines)
    for i, line in enumerate(lines):
        if re.match(r'^_s\d+ = APIRouter\(', line):
            end_idx = i
            break
    return lines[:end_idx]


def split_router_file(filepath, groups, output_dir):
    """
    Split a router file into smaller files based on groups.
    groups: dict of {target_name: [sub_router_nums]}
    """
    lines, sub_routers = parse_subrouters(filepath)
    import_block = get_import_block(lines)
    sr_map = {sr['num']: sr for sr in sub_routers}
    
    created_files = []
    
    for target_name, sr_nums in groups.items():
        ranges = []
        for num in sr_nums:
            if num in sr_map:
                sr = sr_map[num]
                ranges.append((sr['start_idx'], sr['end_idx']))
        
        if not ranges:
            continue
        
        ranges.sort()
        
        # Build the new file content
        new_lines = []
        new_lines.append(f'"""Admin {target_name} router — split from {os.path.basename(filepath)}."""\n')
        new_lines.append('\n')
        
        # Add the import block
        new_lines.extend(import_block)
        new_lines.append('\n')
        
        # Add the sub-router definitions and their routes
        for start, end in ranges:
            for i in range(start, end):
                new_lines.append(lines[i])
        
        # Add a main router that includes all sub-routers
        new_lines.append('\n')
        new_lines.append('router = APIRouter()\n')
        new_lines.append('\n')
        
        for num in sr_nums:
            if num in sr_map:
                new_lines.append('try:\n')
                new_lines.append(f'    router.include_router(_s{num})\n')
                new_lines.append('except Exception as _e:\n')
                new_lines.append(f'    import logging as _l; _l.getLogger(__name__).warning("skip subrouter _s{num}: %s", _e)\n')
                new_lines.append('\n')
        
        # Write the new file
        target_path = os.path.join(output_dir, f'{target_name}.py')
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        total_routes = sum(len(sr_map[n]['routes']) for n in sr_nums if n in sr_map)
        created_files.append({
            'file': target_name + '.py',
            'sub_routers': [f'_s{n}' for n in sr_nums if n in sr_map],
            'total_routes': total_routes,
            'lines': len(new_lines)
        })
    
    # Update the original file to import from the new files
    basename = os.path.basename(filepath)
    new_original = []
    new_original.append(f'"""Admin {os.path.splitext(basename)[0]} router — imports from split sub-modules."""\n')
    new_original.append('\n')
    new_original.append('from fastapi import APIRouter\n')
    new_original.append('\n')
    
    for target_name in groups:
        new_original.append(f'from .{target_name} import router as {target_name}_router\n')
    
    new_original.append('\n')
    new_original.append('router = APIRouter()\n')
    new_original.append('\n')
    
    for target_name in groups:
        new_original.append('try:\n')
        new_original.append(f'    router.include_router({target_name}_router)\n')
        new_original.append('except Exception as _e:\n')
        new_original.append(f'    import logging as _l; _l.getLogger(__name__).warning("skip {target_name}_router: %s", _e)\n')
        new_original.append('\n')
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(new_original)
    
    return created_files


def main():
    base = 'backend/modules/admin/routers'
    
    # Define split groups for all 15 files
    split_config = {
        'finance.py': {
            'payments': [0, 1, 2, 3, 4, 5, 30, 31, 34],
            'payouts': [6, 7, 8, 9, 10, 11, 15, 16, 17, 20, 23, 33],
            'commissions': [22, 24, 27],
            'treasury': [12, 13, 14, 18, 19, 21, 25, 26, 28, 29, 32],
        },
        'country.py': {
            'countries': [2, 3, 4, 27, 29],
            'localization': [0, 1, 5, 6, 7, 11, 15, 17, 19, 21, 22, 24, 25, 26, 28, 30],
            'tax': [8, 10, 12, 13, 14, 16, 18, 20, 23],
        },
        'governance.py': {
            'admin': [0, 3, 7, 8, 9, 10, 18, 20, 28, 35],
            'permissions': [34],
            'fraud': [1, 2, 4, 5, 6, 11, 14, 15, 16, 17, 19, 21, 22, 23, 24, 25, 26, 27, 29],
            'risk': [12, 13, 30, 31, 32, 33, 36],
        },
        'catalog.py': {
            'products': [0, 2, 3, 4, 7, 8, 11, 14, 15, 16, 20, 21],
            'categories': [1, 5, 6, 9, 10, 12, 13, 17],
            'search': [18, 19],
        },
        'comms.py': {
            'chat': [],
            'email': [],
            'notifications': [],
            'tickets': [],
        },
        'suppliers.py': {
            'suppliers': [],
            'products': [],
            'documents': [],
        },
        'logistics.py': {
            'shipping': [],
            'tracking': [],
            'partners': [],
        },
        'orders.py': {
            'orders': [],
            'cart': [],
            'disputes': [],
            'returns': [],
        },
        'security.py': {
            'fraud': [],
            'threat': [],
            'auth': [],
        },
        'accounts.py': {
            'accounts': [],
            'identity': [],
            'sessions': [],
        },
        'customers.py': {
            'customers': [],
            'referrals': [],
            'reviews': [],
        },
        'hr.py': {
            'employees': [],
            'payroll': [],
            'hierarchy': [],
        },
        'promotions.py': {
            'coupons': [],
            'banners': [],
            'bogo': [],
        },
        'audit.py': {
            'audit': [],
            'compliance': [],
        },
        'analytics.py': {
            'analytics': [],
            'reports': [],
        },
    }
    
    all_results = {}
    
    for filename, groups in split_config.items():
        filepath = os.path.join(base, filename)
        if not os.path.exists(filepath):
            print(f"SKIP: {filename} not found")
            continue
        
        # Check if file has sub-routers to split
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        if '_s0 = APIRouter(' not in content:
            print(f"SKIP: {filename} has no sub-routers (already small)")
            continue
        
        lines, sub_routers = parse_subrouters(filepath)
        
        # Auto-assign sub-routers to groups based on routes
        if not any(groups.values()):
            # Auto-group by analyzing routes
            groups = auto_group_subrouters(sub_routers, filename)
        
        print(f"\n=== {filename} ===")
        print(f"  Total sub-routers: {len(sub_routers)}")
        print(f"  Total lines: {len(lines)}")
        
        for target_name, sr_nums in groups.items():
            matching = [n for n in sr_nums if n in [sr['num'] for sr in sub_routers]]
            if matching:
                total_routes = sum(len([sr for sr in sub_routers if sr['num'] == n][0]['routes']) for n in matching)
                print(f"  {target_name}.py: {len(matching)} sub-routers, {total_routes} routes")
        
        created = split_router_file(filepath, groups, base)
        all_results[filename] = created
    
    # Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for filename, created in all_results.items():
        print(f"\n{filename}:")
        for cf in created:
            print(f"  {cf['file']}: {cf['total_routes']} routes, {cf['lines']} lines")


def auto_group_subrouters(sub_routers, filename):
    """Auto-group sub-routers by analyzing their routes and prefixes."""
    # Extract the base name
    base = os.path.splitext(filename)[0]
    
    # Common patterns to look for
    patterns = {
        'finance': {
            'payments': ['payment', 'pay', 'card', 'stripe', 'gateway', 'transaction'],
            'payouts': ['payout', 'payouts'],
            'commissions': ['commission', 'affiliate', 'referral_bonus'],
            'treasury': ['treasury', 'treasury', 'ledger', 'accounting', 'balance', 'bank'],
        },
        'country': {
            'countries': ['country', 'countries', 'region'],
            'localization': ['locale', 'language', 'translation', 'currency', 'timezone'],
            'tax': ['tax', 'vat', 'gst', 'duty'],
        },
    }
    
    if base in patterns:
        target_patterns = patterns[base]
        groups = {k: [] for k in target_patterns}
        
        for sr in sub_routers:
            matched = False
            routes_text = ' '.join(sr['routes']).lower() + ' ' + sr['prefix'].lower()
            
            for target, pats in target_patterns.items():
                if any(p in routes_text for p in pats):
                    groups[target].append(sr['num'])
                    matched = True
                    break
            
            if not matched:
                # Put in first group as fallback
                groups[list(groups.keys())[0]].append(sr['num'])
        
        return groups
    
    # Default: split evenly
    nums = [sr['num'] for sr in sub_routers]
    chunk_size = max(1, len(nums) // 4)
    groups = {}
    for i in range(0, len(nums), chunk_size):
        chunk = nums[i:i+chunk_size]
        name = f'part{i//chunk_size}'
        groups[name] = chunk
    
    return groups


if __name__ == '__main__':
    main()
