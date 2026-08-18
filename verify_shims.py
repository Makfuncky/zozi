import sys
sys.path.insert(0, 'D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend')
checks = [
    ('db.database', ['engine', 'SessionLocal', 'Base', 'get_db', 'DATABASE_URL']),
    ('db.base', ['Base']),
    ('db.session', ['get_db']),
    ('db.schemas', ['Product', 'UserOut', 'PaginatedResponse', 'JournalEntryCreate']),
    ('db.transaction', ['SessionLocal', 'engine']),
    ('db.init_db', ['Base', 'seed_data']),
    ('db.create_tables', ['create_tables']),
    ('db.treasury_seeder', ['seed_treasury_system']),
    ('db.database_logging', ['instrument_database_engine', 'get_db_pool_metrics']),
    ('database', ['SessionLocal', 'engine', 'Base', 'get_db']),
]
ok = True
for mod, names in checks:
    try:
        m = __import__(mod, fromlist=names)
        missing = [n for n in names if not hasattr(m, n)]
        if missing:
            print('FAIL', mod, 'missing', missing); ok = False
        else:
            print('OK', mod)
    except Exception as e:
        print('FAIL', mod, type(e).__name__, e); ok = False
print('ALL OK' if ok else 'SOME FAILED')