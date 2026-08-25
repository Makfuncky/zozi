import os
import subprocess

def run_git_show(stash_ref, filepath):
    """Extract a file from git stash."""
    result = subprocess.run(
        ['git', 'show', f'{stash_ref}:{filepath}'],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    return result.stdout


def main():
    stash = 'stash@{0}'
    base = 'backend/modules/admin/routers'
    
    # Define the mapping: domain -> [(source_path, target_name)]
    # These map stash file paths to the split file names
    domain_mapping = {
        'comms.py': [
            ('_extra_files/_legacy.bak/routers/admin_chat.py', 'chat.py'),
            ('_extra_files/_legacy.bak/routers/admin_chat_routes.py', 'chat_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_email.py', 'email.py'),
            ('_extra_files/_legacy.bak/routers/admin_email_routes.py', 'email_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_comms_geography.py', 'geography.py'),
            ('_extra_files/_legacy.bak/routers/admin_comms_messaging.py', 'messaging.py'),
            ('_extra_files/_legacy.bak/routers/admin_comms_unified.py', 'unified.py'),
            ('_extra_files/_legacy.bak/routers/admin_video.py', 'video.py'),
            ('_extra_files/_legacy.bak/routers/admin_video_routes.py', 'video_routes.py'),
            ('_extra_files/_legacy.bak/routers/comms_chat.py', 'comms_chat.py'),
            ('_extra_files/_legacy.bak/routers/comms_unified.py', 'comms_unified.py'),
            ('_extra_files/_legacy.bak/routers/comms_video.py', 'comms_video.py'),
        ],
        'suppliers.py': [
            ('_extra_files/_legacy.bak/routers/admin_suppliers.py', 'supplier_profiles.py'),
            ('_extra_files/_legacy.bak/routers/admin_suppliers_routes.py', 'supplier_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_supplier_reviews.py', 'supplier_reviews.py'),
            ('_extra_files/_legacy.bak/routers/admin_supplier_trading.py', 'supplier_trading.py'),
            ('_extra_files/_legacy.bak/routers/admin_products.py', 'supplier_products.py'),
            ('_extra_files/_legacy.bak/routers/admin_products_routes.py', 'supplier_products_routes.py'),
        ],
        'logistics.py': [
            ('_extra_files/_legacy.bak/routers/admin_logistics.py', 'shipping.py'),
            ('_extra_files/_legacy.bak/routers/admin_logistics_geography.py', 'logistics_geography.py'),
            ('_extra_files/_legacy.bak/routers/admin_logistics_imports.py', 'logistics_imports.py'),
            ('_extra_files/_legacy.bak/routers/admin_logistics_operations.py', 'logistics_operations.py'),
            ('_extra_files/_legacy.bak/routers/admin_logistics_routes.py', 'logistics_routes.py'),
        ],
        'orders.py': [
            ('_extra_files/_legacy.bak/routers/admin_orders.py', 'orders.py'),
            ('_extra_files/_legacy.bak/routers/admin_orders_routes.py', 'orders_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_orders_status.py', 'orders_status.py'),
        ],
        'security.py': [
            ('_extra_files/_legacy.bak/routers/admin_security_detection.py', 'detection.py'),
            ('_extra_files/_legacy.bak/routers/admin_security_health.py', 'health.py'),
            ('_extra_files/_legacy.bak/routers/admin_security_operations.py', 'operations.py'),
            ('_extra_files/_legacy.bak/routers/admin_security_registration.py', 'registration.py'),
        ],
        'accounts.py': [
            ('_extra_files/_legacy.bak/routers/admin_users.py', 'users.py'),
            ('_extra_files/_legacy.bak/routers/admin_users_routes.py', 'users_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_identity_operations.py', 'identity.py'),
            ('_extra_files/_legacy.bak/routers/admin_identity_operations_api.py', 'identity_api.py'),
        ],
        'customers.py': [
            ('_extra_files/_legacy.bak/routers/admin_customers_router.py', 'customers.py'),
        ],
        'hr.py': [
            ('_extra_files/_legacy.bak/routers/admin_hierarchy_router.py', 'hierarchy.py'),
            ('_extra_files/_legacy.bak/routers/admin_staff_router.py', 'staff.py'),
        ],
        'promotions.py': [
            ('_extra_files/_legacy.bak/routers/admin_promotions.py', 'promotions.py'),
            ('_extra_files/_legacy.bak/routers/admin_promotions_router.py', 'promotions_router.py'),
            ('_extra_files/_legacy.bak/routers/admin_promotions_routes.py', 'promotions_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_banners.py', 'banners.py'),
            ('_extra_files/_legacy.bak/routers/admin_banners_routes.py', 'banners_routes.py'),
            ('_extra_files/_legacy.bak/routers/admin_coupons_router.py', 'coupons.py'),
            ('_extra_files/_legacy.bak/routers/admin_flash_sales_router.py', 'flash_sales.py'),
        ],
        'audit.py': [
            ('_extra_files/_legacy.bak/routers/audit.py', 'audit.py'),
            ('_extra_files/_legacy.bak/routers/admin_geography_audit.py', 'geography_audit.py'),
        ],
        'analytics.py': [
            ('_extra_files/_legacy.bak/routers/admin_analytics_routes.py', 'analytics.py'),
            ('_extra_files/_legacy.bak/routers/admin_analytics_fallback_dashboard.py', 'fallback_dashboard.py'),
        ],
    }
    
    for main_file, sources in domain_mapping.items():
        print(f"\n=== {main_file} ===")
        
        for source_path, target_name in sources:
            content = run_git_show(stash, source_path)
            if content:
                target_path = os.path.join(base, target_name)
                with open(target_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  Extracted {target_name} ({len(content)} bytes)")
            else:
                print(f"  FAILED to extract {source_path}")


if __name__ == '__main__':
    main()
