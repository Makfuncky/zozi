"""Check a specific SQLite database file"""
import sqlite3
import pathlib
import shutil
import tempfile

dbf = pathlib.Path('f:/recovery_recuva_4/Projects/10- E-COMMERCE WEBSITE/backup_20260416_072755_650bca.sqlite')
print(f'File: {dbf.name}')
print(f'Exists: {dbf.exists()}')

if dbf.exists():
    data = dbf.read_bytes()
    print(f'Size: {len(data)/1024:.1f}KB')
    print(f'First bytes: {list(data[:16])}')
    isnull = all(b==0 for b in data[:200])
    print(f'All null: {isnull}')
    
    if not isnull:
        tmp = pathlib.Path(tempfile.mkdtemp()) / 'check.db'
        shutil.copy(dbf, tmp)
        try:
            conn = sqlite3.connect(str(tmp))
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            print(f'Tables: {len(tables)}')
            for t in tables:
                try:
                    count = conn.execute(f'SELECT COUNT(*) FROM "{t[0]}"').fetchone()[0]
                    print(f'  {t[0]}: {count} rows')
                except Exception as e:
                    print(f'  {t[0]}: error - {e}')
            conn.close()
        except Exception as e:
            print(f'SQLite error: {e}')
