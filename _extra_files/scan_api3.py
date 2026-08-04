import ctypes
from ctypes import wintypes
import os, re

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

base = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend'
routers_dir = base + r'\routers'

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
    
    # Find ws_chat or communication references
    for i, line in enumerate(text.split('\n')):
        l = line.lower()
        if 'ws_chat' in l or 'communication' in l:
            print(f'  Line {i+1}: {line.strip()[:120]}')

# Check known router files
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

print('\n--- Flat router files ---')
existing = []
missing = []
for name in known_routers:
    path = routers_dir + '\\' + name + '.py'
    if file_exists(path):
        size = file_size(path)
        existing.append((name, size))
    else:
        missing.append(name)

print(f'Existing: {len(existing)}')
for name, size in sorted(existing):
    print(f'  {name}.py ({size} bytes)')
print(f'Missing: {len(missing)}')
for name in sorted(missing):
    print(f'  {name}.py')

# Check subfolders
subfolders = ['admin', 'ai', 'analytics', 'audit', 'catalog', 'commerce',
              'communication', 'core', 'country', 'customer', 'external',
              'finance', 'hr', 'internal', 'logistics', 'media', 'orders',
              'public', 'security', 'supplier', 'treasury']

print('\n--- Subfolder check ---')
for sf in subfolders:
    path = routers_dir + '\\' + sf
    if file_exists(path):
        print(f'  {sf}/: EXISTS (should have been deleted)')

# Check auth.py - shim or full implementation?
print('\n--- auth.py ---')
auth_path = routers_dir + '\\auth.py'
if file_exists(auth_path):
    content = read_file(auth_path)
    if content:
        text = content.decode('utf-8', errors='replace')
        if 'from data.routers_security_auth import' in text:
            print('SHIM - imports from data.routers_security_auth')
        elif 'APIRouter' in text:
            print('FULL IMPLEMENTATION')
            print(f'Size: {len(content)} bytes')
        else:
            print('UNKNOWN type')
            print(f'Size: {len(content)} bytes')
        print(f'First 300 chars:')
        print(text[:300])

# Check security/auth.py
print('\n--- security/auth.py (original) ---')
sec_auth = routers_dir + '\\security\\auth.py'
exists = file_exists(sec_auth)
print(f'Exists: {exists}')
if exists:
    content = read_file(sec_auth)
    if content:
        print(f'Size: {len(content)} bytes')

# Check forwarder files
data_dir = base + r'\data'
print('\n--- Forwarder files ---')
forwarders = [
    'routers_security_auth',
    'routers_hr_governance',
    'services_command_center_background',
    'auto_payout_scheduler',
]
for f in forwarders:
    path = data_dir + '\\' + f + '.py'
    if file_exists(path):
        content = read_file(path)
        if content:
            text = content.decode('utf-8', errors='replace')
            print(f'{f}.py ({len(content)} bytes):')
            print(f'  {text[:200]}')
