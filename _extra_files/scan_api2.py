import ctypes
from ctypes import wintypes
import os, re, json

kernel32 = ctypes.windll.kernel32

def file_exists(path):
    attrs = kernel32.GetFileAttributesW(path, 0)
    return attrs != 0

def file_size(path):
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        return None
    size = kernel32.GetFileSize(handle, 0)
    kernel32.CloseHandle(handle)
    return size

def read_file(path):
    handle = kernel32.CreateFileW(path, 0x80000000, 1, 0, 3, 0, 0)
    if handle == 0 or handle == -1 or handle == 0xFFFFFFFF:
        return None
    size = kernel32.GetFileSize(handle, 0)
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    return data.raw[:read.value]

# Base path
base = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend'

# Read main.py
main_path = base + r'\main.py'
content = read_file(main_path)
if content:
    text = content.decode('utf-8', errors='replace')
    print(f'main.py: {len(content)} bytes')
    
    # Find router_names list
    for match in re.finditer(r'router_names\s*=\s*\[(.*?)\]', text, re.DOTALL):
        names_text = match.group(1)
        names = re.findall(r'"([^"]+)"', names_text)
        print(f'\n{len(names)} routers in router_names:')
        for n in sorted(names):
            print(f'  {n}')
        break
    
    # Find ws_chat import
    for i, line in enumerate(text.split('\n')):
        if 'ws_chat' in line or 'communication' in line.lower():
            print(f'  Line {i+1}: {line.strip()[:100]}')

# Check each router file
routers_dir = base + r'\routers'
print('\n--- Router files ---')
router_files_to_check = []

# Use a list of all possible router file names
import subprocess

# Try using PowerShell to list files
result = subprocess.run(
    ['powershell', '-Command', 
     f'Get-ChildItem -Path "{routers_dir}" -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName'],
    capture_output=True, text=True
)
if result.returncode == 0 and result.stdout.strip():
    ps_files = [f.strip() for f in result.stdout.strip().split('\n') if f.strip()]
    print(f'PowerShell found {len(ps_files)} .py files')
    
    # Check which are flat vs subdirectory
    flat = [f for f in ps_files if f.count('\\') == f.count('\\routers\\') + 1]
    subdirs = set()
    for f in ps_files:
        rel = f.replace(routers_dir + '\\', '')
        if '\\' in rel:
            subdirs.add(rel.split('\\')[0])
    
    print(f'  Flat files: {len([f for f in ps_files if f.replace(routers_dir+f"\\",'').count("/")==0 and f.replace(routers_dir,"",1).count("/") == 1])}')
    # Actually let's simplify
    flat_count = 0
    sub_dirs = set()
    for f in ps_files:
        if f.startswith(routers_dir + '\\'):
            rel = f[len(routers_dir)+1:]
            if '\\' in rel:
                sub_dirs.add(rel.split('\\')[0])
            else:
                flat_count += 1
    
    print(f'  Flat files: {flat_count}')
    print(f'  Subdirectories with .py files: {sorted(sub_dirs)}')
else:
    print(f'PowerShell error: {result.stderr}')
    # Try another approach - check specific files
    known_routers = [
        'auth', 'admin_audit', 'admin_categories', 'admin_cash', 'admin_chat',
        'admin_commission', 'admin_email', 'admin_fallback', 'admin_logistics',
        'admin_orders', 'admin_permissions', 'admin_products', 'admin_security',
        'admin_settings', 'admin_treasury', 'ai_research_jobs', 'analytics',
        'audit_events', 'catalog', 'catalog_brand', 'catalog_categories',
        'catalog_products', 'checkout', 'communication', 'commerce', 'core',
        'country', 'countries', 'country_auto_populate', 'country_config',
        'customer', 'customer_addresses', 'customer_auth', 'customer_cards',
        'customer_cart', 'customer_orders', 'customer_payouts', 'customer_payments',
        'customer_profile', 'customer_wishlist', 'dashboard', 'ecommerce',
        'email', 'finance', 'hr', 'internal', 'invoices', 'logistics',
        'logistics_tracking', 'media', 'media_assets', 'orders', 'orders_items',
        'payouts', 'public', 'reviews', 'search', 'security', 'shipments',
        'supplier', 'supplier_analytics', 'supplier_brands', 'supplier_countries',
        'supplier_dashboard', 'supplier_documents', 'supplier_finance',
        'supplier_health', 'supplier_onboarding', 'supplier_orders',
        'supplier_payouts', 'supplier_products', 'supplier_profile',
        'treasury', 'treasury_disbursements', 'treasury_settlements',
        'ws_chat'
    ]
    
    print('\nChecking flat router files:')
    existing = []
    missing = []
    for name in known_routers:
        path = routers_dir + rf'\{name}.py'
        if file_exists(path):
            size = file_size(path)
            existing.append((name, size))
        else:
            missing.append(name)
    
    print(f'  Existing: {len(existing)}')
    for name, size in sorted(existing):
        print(f'    {name}.py ({size} bytes)')
    print(f'  Missing: {len(missing)}')
    for name in sorted(missing):
        print(f'    {name}.py')
