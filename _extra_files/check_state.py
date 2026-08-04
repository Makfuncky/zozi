import ctypes, os, json, pathlib

kernel32 = ctypes.windll.kernel32

def file_exists(path):
    return kernel32.GetFileAttributesW(path, 0) != 0

def list_dir(path):
    """List directory using Windows API."""
    results = []
    pattern = path + '\\*'
    handle = kernel32.FindFirstFileW(pattern, None)
    if handle == -1 or handle == 0xFFFFFFFF:
        err = kernel32.GetLastError()
        return [], f'FindFirstFileW failed (error {err})'
    
    # Use a better approach - FindFirstFileW with WIN32_FIND_DATA
    # Actually, let me use ctypes more properly
    return results

def read_file(path):
    handle = kernel32.CreateFileW(
        path, 0x80000000, 1, 0, 3, 0, 0
    )
    if handle == -1 or handle == 0xFFFFFFFF:
        return None, f'CreateFileW failed'
    size = kernel32.GetFileSize(handle, 0)
    data = ctypes.create_string_buffer(size)
    read = ctypes.c_ulong(0)
    kernel32.ReadFile(handle, data, size, ctypes.byref(read), 0)
    kernel32.CloseHandle(handle)
    return data.raw[:read.value], None

# Use a different approach - use subprocess with cmd to list
import subprocess

# Check routers directory via findstr
base = r'D:\Projects/10- E-COMMERCE_WEBSITE\zozi\backend'
print(f'Base: {base}')
print(f'Exists: {file_exists(base)}')

# List via Python's glob (which may work differently)
import glob
py_files = glob.glob(base + r'\routers\*.py')
print(f'\nRouters .py files (glob): {len(py_files)}')
for f in sorted(py_files)[:10]:
    print(f'  {os.path.basename(f)}')

# Check if subfolder directories exist
subfolders = ['admin', 'ai', 'analytics', 'audit', 'catalog', 'commerce', 
              'communication', 'core', 'country', 'customer', 'external',
              'finance', 'hr', 'internal', 'logistics', 'media', 'orders', 
              'public', 'security', 'supplier', 'treasury']

print('\nSubfolder check:')
for sf in subfolders:
    path = base + rf'\routers\{sf}'
    exists = file_exists(path)
    if exists:
        print(f'  {sf}/ EXISTS (should have been deleted)')

# Check flat files that should exist
flat_files = [
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
    'supplier_products', 'treasury', 'treasury_disbursements',
    'treasury_settlements', 'ws_chat',
]

# Check a sample of flat files
print('\nSample flat files check:')
for name in flat_files[:20]:
    path = base + rf'\routers\{name}.py'
    exists = file_exists(path)
    print(f'  {name}.py: {"EXISTS" if exists else "MISSING"}')

# Check auth.py specifically
auth_path = base + r'\routers\auth.py'
if file_exists(auth_path):
    content, err = read_file(auth_path)
    if content:
        text = content.decode('utf-8', errors='replace')
        print(f'\nauth.py: {len(content)} bytes')
        print(f'First 500 chars: {text[:500]}')
