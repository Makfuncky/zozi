"""Comprehensive country domain architecture audit."""
import os
import re

base = r'D:\Projects\10- E-COMMERCE WEBSITE\zozi\backend\domains\country'
issues = []

def check_file(path, content, rel_path):
    lines = content.split('\n')
    in_function = False
    func_indent = 0
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # Track function boundaries
        if stripped.startswith('def ') or stripped.startswith('async def '):
            in_function = True
            func_indent = len(line) - len(line.lstrip())
        elif in_function and stripped and not stripped.startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= func_indent and stripped:
                in_function = False
        
        # Law 1: Domains never import modules (module-level only)
        if re.match(r'^(from|import)\s+modules\.', stripped) and not in_function:
            issues.append(f'{rel_path}:{i} LAW1: Domain imports modules: {stripped}')
        
        # Law 1: Domains never import middleware (module-level only)
        if re.match(r'^(from|import)\s+middleware\.', stripped) and not in_function:
            issues.append(f'{rel_path}:{i} LAW1: Domain imports middleware: {stripped}')
        
        # Law 3: Cross-domain imports (not via ports.py)
        cross_domain = re.match(r'^(from|import)\s+domains\.(governance|orders|catalog|logistics|finance|suppliers|customers|hr|comms|accounts|media|payments)\.', stripped)
        if cross_domain:
            if 'domains.country.' not in stripped:
                if in_function:
                    issues.append(f'{rel_path}:{i} LAW3: Cross-domain import (function-level, use ports): {stripped}')
                else:
                    issues.append(f'{rel_path}:{i} LAW3: Cross-domain import (module-level): {stripped}')
        
        # Law 6: Schema violations
        if '__table_args__' in stripped:
            if "{'schema': 'hr'}" in stripped or "{'schema': 'hr'}" in stripped:
                issues.append(f'{rel_path}:{i} LAW6: Wrong schema (hr): {stripped}')
            if "{'schema': 'configuration'}" in stripped:
                issues.append(f'{rel_path}:{i} LAW6: Wrong schema (configuration): {stripped}')
            if "{'schema': 'treasury'}" in stripped:
                issues.append(f'{rel_path}:{i} LAW6: Wrong schema (treasury): {stripped}')
            if "{'schema': 'logistics'}" in stripped:
                issues.append(f'{rel_path}:{i} LAW6: Wrong schema (logistics): {stripped}')
        
        # Law 8: FK to forbidden schemas
        if 'ForeignKey("core.' in stripped:
            issues.append(f'{rel_path}:{i} LAW8: FK to core: {stripped}')
        if 'ForeignKey("platform.' in stripped:
            issues.append(f'{rel_path}:{i} LAW8: FK to platform: {stripped}')
        if 'ForeignKey("identity.' in stripped:
            issues.append(f'{rel_path}:{i} LAW8: FK to identity: {stripped}')

# Walk all files
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d != '__pycache__']
    for f in files:
        if not f.endswith('.py'): continue
        path = os.path.join(root, f)
        rel_path = os.path.relpath(path, base)
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
            check_file(path, content, rel_path)
        except Exception as e:
            print(f'ERROR reading {rel_path}: {e}')

# Print results
issues.sort()
for issue in issues:
    print(issue)
print(f'\nTotal issues found: {len(issues)}')
