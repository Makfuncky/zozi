import urllib.request
import json

# Test all backend routes from main.py
public_routes = [
    '/', '/health', '/products', '/countries', '/flash-sales', '/banners',
    '/auth', '/users', '/orders', '/cart', '/wishlist', '/addresses',
    '/notifications', '/coupons', '/tickets', '/returns', '/search',
    '/public-suppliers', '/supplier', '/supplier/profile', '/supplier/products',
    '/supplier/orders', '/supplier/payouts', '/supplier/documents', '/supplier/analytics',
    '/logistics', '/logistics/orders', '/logistics/partner', '/contact',
    '/currency/context', '/refund', '/payments', '/reviews', '/banners',
]

admin_routes = [
    '/admin/users', '/admin/orders', '/admin/products', '/admin/analytics',
    '/admin/settings', '/admin/email', '/admin/logistics', '/admin/commission',
    '/admin/cash', '/admin/finance', '/admin/treasury', '/admin/compliance',
    '/admin/expenses', '/admin/iam', '/admin/risk', '/admin/lms',
    '/admin/comm', '/admin/video', '/admin/chat', '/admin/messaging',
    '/admin/hr', '/admin',
]

print('=== PUBLIC ROUTES ===')
for route in public_routes:
    try:
        req = urllib.request.urlopen(f'http://localhost:8000{route}', timeout=3)
        print(f'OK: {route} - Status {req.status}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}: {route}')
    except Exception as e:
        print(f'ERROR: {route} - {str(e)[:40]}')

print()
print('=== ADMIN ROUTES ===')
for route in admin_routes:
    try:
        req = urllib.request.urlopen(f'http://localhost:8000{route}', timeout=3)
        print(f'OK: {route} - Status {req.status}')
    except urllib.error.HTTPError as e:
        print(f'HTTP {e.code}: {route}')
    except Exception as e:
        print(f'ERROR: {route} - {str(e)[:40]}')
