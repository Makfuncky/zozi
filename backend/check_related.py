"""
ZOZI Database & API Fix Plan

Root Causes Identified:
1. CountryConfig model has cross-domain relationships (ShippingRule, PayoutRule, TaxRule, User, etc.)
   that aren't loaded when SQLAlchemy configures the mapper
2. Model loading order issue - cross-domain models need to be imported before relationships are configured

Fix Strategy:
1. Import all models in the correct order before configuring relationships
2. Use deferred relationship configuration or ensure all models are registered
3. Test each fix step by step
"""

import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()

# Check which related tables exist
related_tables = [
    'shipping_rules', 'payout_rules', 'tax_rules', 'country_category_tax_rates',
    'country_feature_flags', 'country_staff_assignments', 'country_config_versions',
    'country_commission_rates', 'supplier_kyc_requirements', 'logistics_partner_kyc_requirements',
    'country_cities', 'country_basics', 'country_economics', 'country_legal', 'country_tax',
    'tax_rules', 'users'
]

print("=== Related Tables Check ===")
for table in related_tables:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} rows")
    except Exception as e:
        print(f"  {table}: MISSING - {e}")

conn.close()
