import os, sys
sys.stdout.reconfigure(encoding='utf-8')

unmapped = [
    ('admin', 'admin_categories'),
    ('admin', 'admin_treasury'),
    ('admin', 'cash_management'),
    ('admin', 'command_center_api'),
    ('admin', 'country_communications'),
    ('admin', 'country_versioning'),
    ('admin', 'employees'),
    ('communication', 'chat_api'),
    ('communication', 'email_router'),
    ('communication', 'video_router'),
    ('finance', 'invoices'),
    ('hr', 'command_center_router'),
    ('hr', 'governance'),
    ('internal', 'expenses'),
    ('internal', 'finance_domain'),
    ('internal', 'health'),
    ('internal', 'messaging'),
    ('internal', 'treasury_api'),
    ('security', 'auth'),
    ('supplier', 'finance'),
]

with open('backend/main.py', encoding='utf-8') as f:
    main_content = f.read()

for subfolder, module in unmapped:
    flat_path = f'backend/routers/{module}.py'
    sub_path = f'backend/routers/{subfolder}/{module}.py'
    
    flat_exists = os.path.exists(flat_path)
    sub_exists = os.path.exists(sub_path)
    
    in_main = f'"{module}"' in main_content or f"'{module}'" in main_content
    
    flat_content = ''
    if flat_exists:
        with open(flat_path, encoding='utf-8') as f:
            flat_content = f.read().strip()[:80]
    
    sub_content = ''
    if sub_exists:
        with open(sub_path, encoding='utf-8') as f:
            sub_content = f.read().strip()[:80]
    
    print(f'{subfolder}/{module}.py:')
    print(f'  Flat file exists: {flat_exists} -> {flat_content!r}')
    print(f'  Subfolder exists: {sub_exists} -> {sub_content!r}')
    print(f'  In main.py: {in_main}')
    print()
