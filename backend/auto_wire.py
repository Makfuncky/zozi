"""
Auto Wire — Fixes router imports using the Service Registry.
Works with the canonical router structure: modules/{m}/routers/{d}.py
"""
import re
from pathlib import Path
from collections import defaultdict
from registry import ServiceRegistry

BACKEND = Path(__file__).parent
MODULES = BACKEND / 'modules'

MODULES_LIST = ['admin', 'customer', 'employee', 'logistics', 'supplier']


def fix_imports(corrections, dry_run=True):
    """Fix imports that point to wrong paths."""
    by_file = defaultdict(list)
    for item in corrections:
        by_file[item['full_path']].append(item)
    
    fixed = 0
    total = 0
    
    for filepath, items in by_file.items():
        f = BACKEND / filepath
        if not f.exists():
            continue
        
        content = f.read_text(encoding='utf-8', errors='replace')
        original = content
        
        for item in items:
            old_import = f'from {item["old_path"]} import {item["name"]}'
            new_import = f'from {item["new_path"]} import {item["name"]}'
            old_import_aliased = f'from {item["old_path"]} import {item["name"]} as '
            
            if old_import in content:
                content = content.replace(old_import, new_import)
                total += 1
                if dry_run:
                    print(f'  {filepath}:')
                    print(f'    {old_import}')
                    print(f'    -> {new_import}')
            elif old_import_aliased in content:
                content = content.replace(old_import_aliased, f'from {item["new_path"]} import {item["name"]} as ')
                total += 1
                if dry_run:
                    print(f'  {filepath}:')
                    print(f'    {old_import_aliased}...')
                    print(f'    -> {item["new_path"]}')
        
        if content != original and not dry_run:
            f.write_text(content, encoding='utf-8')
            fixed += 1
    
    return fixed, total


def generate_stubs(missing, dry_run=True):
    """Generate stub files for truly missing services."""
    DOMAINS = BACKEND / 'domains'
    
    by_domain = defaultdict(set)
    for item in missing:
        by_domain[item['domain']].add(item['name'])
    
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
        lines.append('TODO: Replace with real implementations.')
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
    
    print('=' * 60)
    print('AUTO WIRE')
    print('=' * 60)
    
    # Build registry
    reg = ServiceRegistry()
    count = reg.scan()
    print(f'\nIndexed {count} services')
    
    # Get corrections and missing
    corrections = reg.get_import_corrections()
    missing = reg.get_missing_services()
    
    print(f'Import corrections: {len(corrections)}')
    print(f'Missing services: {len(missing)}')
    
    if dry_run:
        print('\n--- DRY RUN ---')
    else:
        print('\n--- APPLYING ---')
    
    print('\n[1] Fixing imports...')
    fixed, total = fix_imports(corrections, dry_run=dry_run)
    
    print(f'\n[2] Generating stubs...')
    stubs = generate_stubs(missing, dry_run=dry_run)
    
    if dry_run:
        print(f'\nRun with --apply to:')
        print(f'  Fix: {total} imports in {len(set(c["full_path"] for c in corrections))} files')
        print(f'  Generate: {len(stubs)} stub files')
    else:
        print(f'\nComplete:')
        print(f'  Fixed: {total} imports in {fixed} files')
        print(f'  Generated: {len(stubs)} stub files')
    
    # Save registry
    reg.save()


if __name__ == '__main__':
    main()
