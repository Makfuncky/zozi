import sys
sys.path.insert(0, 'D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend')
for mod in ['db.database', 'db.base', 'db.session', 'db.schemas', 'db.transaction', 'db.init_db', 'db.create_tables', 'db.treasury_seeder', 'db.database_logging']:
    try:
        __import__(mod, fromlist=['x'])
        import database
        ok = hasattr(database, 'SessionLocal')
        print(f'{mod:24s} -> database.SessionLocal={ok}  file={database.__file__}')
    except Exception as e:
        print(f'{mod:24s} -> EXC {type(e).__name__}: {e}')