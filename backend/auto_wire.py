"""
Complete automatic wiring system:
1. Build registry index
2. Fix imports that point to wrong paths
3. Generate stubs for truly missing services
"""
import re
import json
from pathlib import Path
from collections import defaultdict

BACKEND = Path('D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend')
DOMAINS = BACKEND / 'domains'
MODULES = BACKEND / 'modules'
INFRA = BACKEND / 'infrastructure'
PROVIDERS = BACKEND / 'providers'

MODULES_LIST = ['admin', 'customer', 'employee', 'logistics', 'supplier']

# Canonical domain files (for reference)
CANONICAL_DOMAINS = ['accounts', 'analytics', 'audit', 'catalog', 'comms', 'country',
                     'customers', 'finance', 'governance', 'hr', 'logistics', 'orders',
                     'promotions', 'security', 'suppliers']


def build_index():
    """Build index of all existing services."""
    index = {}
    for base, prefix in [(DOMAINS, 'domains'), (INFRA, 'infrastructure'), (PROVIDERS, 'providers')]:
        if not base.exists():
            continue
        for domain_dir in sorted(base.iterdir()):
            if not domain_dir.is_dir():
                continue
            for f in sorted(domain_dir.rglob('*.py')):
                if f.name == '__init__.py':
                    continue
                relative = f.relative_to(domain_dir)
                module_path = f'{prefix}.{domain_dir.name}.' + '.'.join(relative.with_suffix('').parts)
                
                try:
                    content = f.read_text(encoding='utf-8', errors='replace')
                    for m in re.finditer(r'^(?:def|class)\s+(\w+)\s*[\(:]', content, re.MULTILINE):
                        name = m.group(1)
                        # Index ALL names (including private) for import resolution
                        if name not in index:
                            index[name] = module_path
                except Exception:
                    pass
    return index


def check_path_exists(import_path):
    """Check if a module path exists."""
    parts = import_path.split('.')
    if parts[0] == 'domains':
        base = DOMAINS
        parts = parts[1:]
    elif parts[0] == 'infrastructure':
        base = INFRA
        parts = parts[1:]
    elif parts[0] == 'providers':
        base = PROVIDERS
        parts = parts[1:]
    else:
        return False
    
    current = base
    for part in parts:
        current = current / part
    
    return current.with_suffix('.py').exists() or (current.exists() and current.is_dir())


def scan_imports():
    """Scan all router imports and categorize them."""
    index = build_index()
    
    wrong_path = []
    truly_missing = []
    
    for module in MODULES_LIST:
        routers_dir = MODULES / module / 'routers'
        if not routers_dir.exists():
            continue
        
        for f in sorted(routers_dir.glob('*.py')):
            if f.name == '__init__.py':
                continue
            
            try:
                content = f.read_text(encoding='utf-8', errors='replace')
            except Exception:
                continue
            
            for line_num, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                m = re.match(r'^from (domains\.\w+(?:\.\w+)*) import (.+)$', line)
                if not m:
                    continue
                
                path = m.group(1)
                names_str = m.group(2)
                
                names = []
                for name in names_str.split(','):
                    name = name.strip()
                    if not name or name in ('*', 'noqa', 'F401', 'F403') or name.startswith('#'):
                        continue
                    if ' as ' in name:
                        name = name.split(' as ')[0].strip()
                    names.append(name)
                
                if not check_path_exists(path):
                    for name in names:
                        if name in index:
                            wrong_path.append({
                                'file': f'{module}/{f.name}',
                                'line': line_num,
                                'name': name,
                                'old_path': path,
                                'new_path': index[name]
                            })
                        else:
                            truly_missing.append({
                                'file': f'{module}/{f.name}',
                                'line': line_num,
                                'name': name,
                                'old_path': path
                            })
    
    return wrong_path, truly_missing


def fix_wrong_paths(wrong_path, dry_run=True):
    """Fix imports that point to wrong paths."""
    by_file = defaultdict(list)
    for item in wrong_path:
        # Fix path: modules/{module}/routers/{file}
        parts = item['file'].split('/')
        item['full_path'] = f'modules/{parts[0]}/routers/{parts[1]}'
        by_file[item['full_path']].append(item)
    
    fixed = 0
    total_corrections = 0
    
    for filepath, items in by_file.items():
        f = BACKEND / filepath
        if not f.exists():
            print(f'  File not found: {filepath}')
            continue
        
        content = f.read_text(encoding='utf-8', errors='replace')
        original = content
        
        for item in items:
            old_import = f'from {item["old_path"]} import {item["name"]}'
            new_import = f'from {item["new_path"]} import {item["name"]}'
            old_import_aliased = f'from {item["old_path"]} import {item["name"]} as '
            
            if old_import in content:
                content = content.replace(old_import, new_import)
                total_corrections += 1
                if dry_run:
                    print(f'  {filepath}: {old_import}')
                    print(f'         -> {new_import}')
            elif old_import_aliased in content:
                content = content.replace(old_import_aliased, f'from {item["new_path"]} import {item["name"]} as ')
                total_corrections += 1
                if dry_run:
                    print(f'  {filepath}: {old_import_aliased}...')
                    print(f'         -> {item["new_path"]}')
        
        if content != original and not dry_run:
            f.write_text(content, encoding='utf-8')
            fixed += 1
    
    return fixed, total_corrections


def generate_stubs(truly_missing, dry_run=True):
    """Generate stub files for truly missing services."""
    by_domain = defaultdict(set)
    for item in truly_missing:
        domain = item['old_path'].split('.')[1] if len(item['old_path'].split('.')) > 1 else 'unknown'
        by_domain[domain].add(item['name'])
    
    generated = []
    for domain, names in sorted(by_domain.items()):
        domain_dir = DOMAINS / domain
        if not domain_dir.exists():
            continue
        
        services_dir = domain_dir / 'services'
        if not services_dir.exists():
            services_dir.mkdir(exist_ok=True)
            (services_dir / '__init__.py').write_text('', encoding='utf-8')
        
        stub_file = services_dir / '_auto_stubs.py'
        
        lines = []
        lines.append('"""')
        lines.append(f'Auto-generated stub services for {domain} domain.')
        lines.append('TODO: Replace these stubs with real implementations.')
        lines.append('"""')
        lines.append('')
        
        for name in sorted(names):
            if name[0].isupper():
                lines.append(f'class {name}:')
                lines.append(f'    """TODO: Implement."""')
                lines.append(f'    pass')
                lines.append(f'')
            else:
                lines.append(f'def {name}(**kwargs):')
                lines.append(f'    """TODO: Implement."""')
                lines.append(f'    return {{}}')
                lines.append(f'')
        
        content = '\n'.join(lines)
        
        if not dry_run:
            stub_file.write_text(content, encoding='utf-8')
            generated.append(stub_file)
            print(f'Generated: {stub_file.relative_to(BACKEND)} ({len(names)} stubs)')
        else:
            print(f'Would generate: {stub_file.relative_to(BACKEND)} ({len(names)} stubs)')
            generated.append(stub_file)
    
    return generated


def main():
    import sys
    dry_run = '--apply' not in sys.argv
    
    print('=' * 80)
    print('AUTOMATIC WIRING SYSTEM')
    print('=' * 80)
    
    wrong_path, truly_missing = scan_imports()
    
    print(f'\nImports with wrong path: {len(wrong_path)}')
    print(f'Truly missing services: {len(truly_missing)}')
    
    if dry_run:
        print('\n--- DRY RUN ---')
    else:
        print('\n--- APPLYING ---')
    
    print('\n[1] Fixing wrong paths...')
    fixed, total = fix_wrong_paths(wrong_path, dry_run=dry_run)
    
    print(f'\n[2] Generating stubs for missing services...')
    stubs = generate_stubs(truly_missing, dry_run=dry_run)
    
    if dry_run:
        print(f'\n--- Run with --apply to make changes ---')
        print(f'Would fix: {total} imports in {len(set(item["file"] for item in wrong_path))} files')
        print(f'Would generate: {len(stubs)} stub files')
    else:
        print(f'\n--- Complete ---')
        print(f'Fixed: {total} imports in {fixed} files')
        print(f'Generated: {len(stubs)} stub files')


if __name__ == '__main__':
    main()
