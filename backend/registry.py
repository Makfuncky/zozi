"""
Service Registry — Discovers and indexes all domain services.
Works with the canonical router structure: modules/{m}/routers/{d}.py
"""
import re
import json
from pathlib import Path
from collections import defaultdict

BACKEND = Path(__file__).parent
DOMAINS = BACKEND / 'domains'
MODULES = BACKEND / 'modules'
INFRA = BACKEND / 'infrastructure'
PROVIDERS = BACKEND / 'providers'
INDEX_FILE = BACKEND / 'service_index.json'

MODULES_LIST = ['admin', 'customer', 'employee', 'logistics', 'supplier']
DOMAINS_LIST = ['accounts', 'analytics', 'audit', 'catalog', 'comms', 'country',
                'customers', 'finance', 'governance', 'hr', 'logistics', 'orders',
                'promotions', 'security', 'suppliers']


class ServiceRegistry:
    """Discovers, indexes, and resolves domain services."""
    
    def __init__(self):
        self.index = {}
        self.by_domain = defaultdict(dict)
    
    def scan(self):
        """Scan all domain files and build the index."""
        self.index.clear()
        self.by_domain.clear()
        
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
                            if not name.startswith('_'):
                                if name not in self.index:
                                    self.index[name] = module_path
                                    self.by_domain[domain_dir.name][name] = module_path
                    except Exception:
                        pass
        
        return len(self.index)
    
    def resolve(self, name):
        """Resolve a service name to its import path."""
        return self.index.get(name)
    
    def search(self, query):
        """Search for services by name pattern."""
        return {name: path for name, path in self.index.items() if query.lower() in name.lower()}
    
    def save(self):
        """Persist index to JSON."""
        data = {
            'index': self.index,
            'by_domain': dict(self.by_domain),
            'metadata': {
                'total_services': len(self.index),
                'total_domains': len(self.by_domain),
                'domains': sorted(self.by_domain.keys())
            }
        }
        INDEX_FILE.write_text(json.dumps(data, indent=2), encoding='utf-8')
        return len(self.index)
    
    def load(self):
        """Load index from JSON."""
        if not INDEX_FILE.exists():
            return False
        data = json.loads(INDEX_FILE.read_text(encoding='utf-8'))
        self.index = data['index']
        self.by_domain = defaultdict(dict, data['by_domain'])
        return True
    
    def get_import_corrections(self):
        """Find all router imports that need correction."""
        corrections = []
        
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
                        if not name or name.startswith('#'):
                            continue
                        if ' as ' in name:
                            name = name.split(' as ')[0].strip()
                        if name and name not in ('*', 'noqa', 'F401', 'F403'):
                            names.append(name)
                    
                    for name in names:
                        correct_path = self.resolve(name)
                        if correct_path and correct_path != path:
                            corrections.append({
                                'file': f'{module}/{f.name}',
                                'full_path': f'modules/{module}/routers/{f.name}',
                                'line': line_num,
                                'name': name,
                                'old_path': path,
                                'new_path': correct_path
                            })
        
        return corrections
    
    def get_missing_services(self):
        """Find imports where the service doesn't exist anywhere."""
        missing = []
        
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
                        if not name or name.startswith('#'):
                            continue
                        if ' as ' in name:
                            name = name.split(' as ')[0].strip()
                        if name and name not in ('*', 'noqa', 'F401', 'F403'):
                            names.append(name)
                    
                    for name in names:
                        if name not in self.index:
                            domain = path.split('.')[1] if len(path.split('.')) > 1 else 'unknown'
                            missing.append({
                                'file': f'{module}/{f.name}',
                                'full_path': f'modules/{module}/routers/{f.name}',
                                'line': line_num,
                                'name': name,
                                'old_path': path,
                                'domain': domain
                            })
        
        return missing
    
    def print_stats(self):
        """Print registry statistics."""
        print(f'Total services indexed: {len(self.index)}')
        print(f'Total domains: {len(self.by_domain)}')
        for domain in sorted(self.by_domain.keys()):
            print(f'  {domain}: {len(self.by_domain[domain])} services')


def main():
    print('=' * 60)
    print('SERVICE REGISTRY')
    print('=' * 60)
    
    reg = ServiceRegistry()
    count = reg.scan()
    reg.save()
    
    print(f'\nIndexed {count} services')
    reg.print_stats()
    
    corrections = reg.get_import_corrections()
    missing = reg.get_missing_services()
    
    print(f'\nImport corrections needed: {len(corrections)}')
    print(f'Missing services: {len(missing)}')


if __name__ == '__main__':
    main()
