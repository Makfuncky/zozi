"""Find routes with empty paths across all admin routers."""
import sys, os, importlib, logging

logging.disable(logging.CRITICAL)
sys.path.insert(0, '.')

# Import the __init__ to get the module list
init = importlib.import_module('modules.admin.routers')

empty_routes = []
for m in init.routers:
    for route in m.routes:
        if hasattr(route, 'path') and route.path == '':
            empty_routes.append(f'{m.__name__}: EMPTY PATH -> {route.name}')

if empty_routes:
    for r in empty_routes:
        print(r)
else:
    print('No empty routes found in loaded routers')

# Also check if admin_banners router loaded
for m in init.routers:
    if 'banners' in m.__name__:
        print(f'Loaded: {m.__name__} prefix={m.prefix}')
