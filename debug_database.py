import sys
sys.path.insert(0, 'D:/Projects/10- E-COMMERCE WEBSITE/zozi/backend')
import db.create_tables
print('db.create_tables file:', db.create_tables.__file__)
import database
print('database file:', database.__file__)
print('database keys:', [n for n in dir(database) if not n.startswith('__')])
import infrastructure.database.database as real
print('real.SessionLocal:', real.SessionLocal)
print('database.SessionLocal via getattr:', getattr(database, 'SessionLocal', 'MISSING'))