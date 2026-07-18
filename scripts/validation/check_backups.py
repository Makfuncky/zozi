"""Check SQLite backup files for integrity and schema"""
import pathlib
import sqlite3
import tempfile
import shutil

backup_dir = pathlib.Path('f:/recovery_recuva_4/Projects/10- E-COMMERCE WEBSITE/zozi/uploads/backups')

backups = sorted([f for f in backup_dir.glob('*.sqlite')], key=lambda x: x.stat().st_mtime)
print(f'Found {len(backups)} backup files')

for backup in backups[-3:]:  # Check last 3 (most recent)
    data = backup.read_bytes()
    is_null = all(b==0 for b in data[:100])
    print(f'\n=== {backup.name} ===')
    print(f'  Size: {len(data)/1024:.1f}KB, null={is_null}')
    print(f'  Magic: {list(data[:16])}')
    
    if not is_null:
        tmp = pathlib.Path(tempfile.mkdtemp()) / 'test.db'
        shutil.copy(backup, tmp)
        try:
            conn = sqlite3.connect(str(tmp))
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
            print(f'  Tables found: {len(tables)}')
            for t in tables:
                try:
                    count = conn.execute(f'SELECT COUNT(*) FROM "{t[0]}"').fetchone()[0]
                    print(f'    {t[0]}: {count} rows')
                except Exception as e:
                    print(f'    {t[0]}: ERROR - {e}')
            conn.close()
        except Exception as e:
            print(f'  sqlite3 error: {e}')
