"""
Phase 19: Router Splitting
Split huge router files into thin, focused routers.
"""
import os

BASE = 'backend/modules/admin/routers'

# Domain split configuration
# Each main file is split into smaller files that import from the extracted sources
SPLIT_CONFIG = {
    'comms.py': {
        'chat': [
            'admin_chat.py',
            'admin_chat_routes.py',
            'chat.py',
            'chat_routes.py',
            'comms_chat.py',
        ],
        'email': [
            'admin_email.py',
            'admin_email_routes.py',
            'email.py',
            'email_routes.py',
            'core_email_routes.py',
        ],
        'notifications': [
            'admin_comms_messaging.py',
            'messaging.py',
            'core_messaging_routes.py',
        ],
        'tickets': [
            'admin_comms_unified.py',
            'unified.py',
            'comms_unified.py',
            'core_video_routes.py',
        ],
    },
    'suppliers.py': {
        'suppliers': [
            'admin_suppliers.py',
            'admin_suppliers_routes.py',
            'supplier_profiles.py',
            'supplier_routes.py',
            'admin_supplier_reviews.py',
            'supplier_reviews.py',
            'admin_supplier_trading.py',
            'supplier_trading.py',
        ],
        'products': [
            'admin_products.py',
            'supplier_products.py',
            'supplier_products_routes.py',
        ],
        'documents': [
            'admin_suppliers_router.py',
            'admin_supplier_reviews.py',
        ],
    },
    'logistics.py': {
        'shipping': [
            'admin_logistics.py',
            'shipping.py',
            'admin_logistics_routes.py',
            'logistics_routes.py',
        ],
        'tracking': [
            'admin_logistics_operations.py',
            'logistics_operations.py',
        ],
        'partners': [
            'admin_logistics_geography.py',
            'logistics_geography.py',
            'admin_logistics_imports.py',
            'logistics_imports.py',
        ],
    },
    'orders.py': {
        'orders': [
            'admin_orders.py',
            'orders.py',
            'admin_orders_routes.py',
            'orders_routes.py',
            'admin_orders_status.py',
            'orders_status.py',
        ],
        'cart': [
            'admin_orders_router.py',
        ],
        'disputes': [
            'admin_disputes_router.py',
        ],
        'returns': [
            'admin_orders_status.py',
        ],
    },
    'security.py': {
        'fraud': [
            'admin_security_detection.py',
            'detection.py',
        ],
        'threat': [
            'admin_security_operations.py',
            'operations.py',
        ],
        'auth': [
            'admin_security_registration.py',
            'registration.py',
            'admin_security_health.py',
            'health.py',
        ],
    },
    'accounts.py': {
        'accounts': [
            'admin_users.py',
            'users.py',
            'admin_users_routes.py',
            'users_routes.py',
            'admin_users_router.py',
        ],
        'identity': [
            'admin_identity_operations.py',
            'identity.py',
            'admin_identity_operations_api.py',
            'identity_api.py',
        ],
        'sessions': [
            'core_users_routes.py',
        ],
    },
    'customers.py': {
        'customers': [
            'admin_customers_router.py',
            'customers.py',
        ],
        'referrals': [
            'public_commerce_referrals.py',
        ],
        'reviews': [
            'admin_supplier_reviews.py',
            'public_commerce_reviews.py',
        ],
    },
    'hr.py': {
        'employees': [
            'admin_staff_router.py',
            'country_staff.py',
        ],
        'payroll': [
            'core_payroll_routes.py',
            'admin_hierarchy_router.py',
        ],
        'hierarchy': [
            'admin_hierarchy_router.py',
            'core_hierarchy_routes.py',
            'public_hr_hierarchy.py',
        ],
    },
    'promotions.py': {
        'coupons': [
            'admin_coupons_router.py',
            'admin_admin_coupons.py',
        ],
        'banners': [
            'admin_banners.py',
            'banners.py',
            'admin_banners_routes.py',
            'banners_routes.py',
        ],
        'bogo': [
            'admin_promotions.py',
            'promotions.py',
            'admin_promotions_routes.py',
            'admin_promotions_router.py',
            'admin_flash_sales_router.py',
        ],
    },
    'audit.py': {
        'audit': [
            'audit.py',
            'admin_audit_router.py',
        ],
        'compliance': [
            'admin_geography_audit.py',
            'geography_audit.py',
            'core_compliance_routes.py',
        ],
    },
    'analytics.py': {
        'analytics': [
            'admin_analytics_routes.py',
            'analytics.py',
            'admin_analytics_router.py',
        ],
        'reports': [
            'admin_analytics_fallback_dashboard.py',
            'admin_analytics.py',
        ],
    },
}


def create_split_file(main_file, split_name, source_files):
    """Create a split file that imports from source files."""
    target_path = os.path.join(BASE, f'{split_name}.py')
    
    content = f'"""Admin {split_name} router — split from {main_file}."""\n'
    content += f'from fastapi import APIRouter\n'
    content += f'from typing import Optional\n'
    content += f'\n'
    content += f'router = APIRouter()\n'
    content += f'\n'
    
    for src in source_files:
        src_module = src.replace('.py', '')
        content += f'try:\n'
        content += f'    from .{src_module} import router as {src_module}_router\n'
        content += f'    router.include_router({src_module}_router)\n'
        content += f'except Exception as _e:\n'
        content += f'    import logging as _l; _l.getLogger(__name__).warning("skip {src_module}: %s", _e)\n'
        content += f'\n'
    
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return target_path


def update_main_file(main_file, split_names):
    """Update the main file to import from split files."""
    target_path = os.path.join(BASE, main_file)
    
    content = f'"""Admin {main_file.replace(".py", "")} router — imports from split sub-modules."""\n'
    content += f'from fastapi import APIRouter\n'
    content += f'\n'
    
    for name in split_names:
        content += f'from .{name} import router as {name}_router\n'
    
    content += f'\n'
    content += f'router = APIRouter()\n'
    content += f'\n'
    
    for name in split_names:
        content += f'try:\n'
        content += f'    router.include_router({name}_router)\n'
        content += f'except Exception as _e:\n'
        content += f'    import logging as _l; _l.getLogger(__name__).warning("skip {name}_router: %s", _e)\n'
        content += f'\n'
    
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return target_path


def main():
    results = {}
    
    for main_file, splits in SPLIT_CONFIG.items():
        print(f"\n=== {main_file} ===")
        
        created_splits = []
        for split_name, source_files in splits.items():
            # Check if source files exist
            existing_sources = []
            for src in source_files:
                src_path = os.path.join(BASE, src)
                if os.path.exists(src_path):
                    existing_sources.append(src)
            
            if existing_sources:
                target = create_split_file(main_file, split_name, existing_sources)
                print(f"  Created {split_name}.py ({len(existing_sources)} sources)")
                created_splits.append(split_name)
            else:
                print(f"  SKIP {split_name}.py (no source files found)")
        
        if created_splits:
            update_main_file(main_file, created_splits)
            print(f"  Updated {main_file}")
            results[main_file] = created_splits
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for main_file, splits in results.items():
        print(f"{main_file}: {', '.join(splits)}")


if __name__ == '__main__':
    main()
