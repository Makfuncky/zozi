#!/usr/bin/env python3
"""Analyze hand-written routers and map them to controllers for migration."""

import ast
import os
import re
from collections import defaultdict

ROOT = "D:\\Projects\\10- E-COMMERCE WEBSITE\\zozi\\backend"
ROUTERS_DIR = os.path.join(ROOT, "routers")
CONTROLLERS_DIR = os.path.join(ROOT, "controllers")
MARKER = "AUTO-GENERATED"

def is_auto_generated(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return MARKER in f.read(500)
    except Exception:
        return False

def get_router_info(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        
        routes = []
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.append(node.module)
            if isinstance(node, ast.FunctionDef):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Attribute):
                        if dec.attr in ('get', 'post', 'put', 'patch', 'delete'):
                            routes.append({
                                'func': node.name,
                                'method': dec.attr.upper(),
                                'path': ast.unparse(dec.args[0]) if dec.args else ''
                            })
        
        return {
            'routes': routes,
            'imports': imports,
            'lines': len(content.split('\n'))
        }
    except Exception as e:
        return {'error': str(e), 'routes': [], 'imports': [], 'lines': 0}

def main():
    routers = []
    for fn in sorted(os.listdir(ROUTERS_DIR)):
        if not fn.endswith('.py') or fn == '__init__.py':
            continue
        fp = os.path.join(ROUTERS_DIR, fn)
        if is_auto_generated(fp):
            continue
        
        info = get_router_info(fp)
        routers.append({
            'file': fn,
            'path': fp,
            **info
        })
    
    # Group by imported controller
    controller_map = defaultdict(list)
    for r in routers:
        for imp in r.get('imports', []):
            if imp.startswith('controllers.'):
                controller_map[imp].append(r['file'])
    
    print(f"Total hand-written routers: {len(routers)}")
    print(f"\nTop controllers by router count:")
    for ctrl, files in sorted(controller_map.items(), key=lambda x: -len(x[1]))[:20]:
        print(f"  {ctrl}: {len(files)} routers")
        for f in files[:5]:
            print(f"    - {f}")
        if len(files) > 5:
            print(f"    ... and {len(files) - 5} more")
    
    # Save detailed report
    with open('router_migration_analysis.txt', 'w') as f:
        f.write(f"Total hand-written routers: {len(routers)}\n\n")
        f.write("Controller -> Router mapping:\n")
        for ctrl, files in sorted(controller_map.items(), key=lambda x: -len(x[1])):
            f.write(f"\n{ctrl} ({len(files)} routers):\n")
            for fn in files:
                f.write(f"  - {fn}\n")
        
        f.write("\n\nAll routers:\n")
        for r in routers:
            f.write(f"\n{r['file']} ({r['lines']} lines, {len(r['routes'])} routes)\n")
            for route in r['routes'][:10]:
                f.write(f"  {route['method']} {route['path']} -> {route['func']}\n")
            if len(r['routes']) > 10:
                f.write(f"  ... and {len(r['routes']) - 10} more routes\n")

if __name__ == '__main__':
    main()
