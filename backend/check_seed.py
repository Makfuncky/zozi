import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()

# Check key tables for seed data
tables_to_check = [
    'users', 'products', 'categories', 'orders', 'suppliers',
    'supplier_profiles', 'customers', 'employees', 'roles',
    'permission_categories', 'country_configs', 'countries',
    'catalog_products', 'catalog_categories'
]

print("=== Seed Data Check ===")
for table in tables_to_check:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    except Exception as e:
        print(f"  {table}: ERROR - {e}")

# Check for demo users specifically
print("\n=== Demo Users ===")
try:
    cursor.execute("SELECT email, role, full_name FROM users WHERE email LIKE '%@zozi.com' OR email LIKE '%@example.com' LIMIT 10")
    users = cursor.fetchall()
    for u in users:
        print(f"  {u[0]} | role={u[1]} | name={u[2]}")
except Exception as e:
    print(f"  ERROR: {e}")

conn.close()
