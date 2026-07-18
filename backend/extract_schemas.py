import sqlite3
conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()

# Get all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

with open('table_schemas.md', 'w', encoding='utf-8') as f:
    f.write("# Complete Database Schema - All 263 Tables\n\n")
    
    for table_name in tables:
        table = table_name[0]
        f.write(f"## `{table}`\n\n")
        
        # Get table info
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        if columns:
            f.write("| Column | Type | NotNull | Default | PK |\n")
            f.write("|--------|------|---------|---------|----|\n")
            for col in columns:
                cid, name, ctype, notnull, default_val, pk = col
                default_str = str(default_val) if default_val is not None else ""
                f.write(f"| {name} | {ctype} | {notnull} | {default_str} | {pk} |\n")
            f.write("\n")
        
        # Get indexes
        cursor.execute(f"PRAGMA index_list({table})")
        indexes = cursor.fetchall()
        if indexes:
            f.write("### Indexes\n\n")
            for idx in indexes:
                f.write(f"- `{idx[1]}` (unique: {bool(idx[2])})\n")
            f.write("\n")
        
        # Get foreign keys
        cursor.execute(f"PRAGMA foreign_key_list({table})")
        fks = cursor.fetchall()
        if fks:
            f.write("### Foreign Keys\n\n")
            for fk in fks:
                f.write(f"- `{fk[3]}` -> `{fk[2]}.{fk[4]}`\n")
            f.write("\n")
        
        # Get sample data (first 3 rows)
        cursor.execute(f"SELECT * FROM {table} LIMIT 3")
        rows = cursor.fetchall()
        if rows:
            col_names = [desc[0] for desc in cursor.description]
            f.write("### Sample Data\n\n")
            f.write("| " + " | ".join(col_names) + " |\n")
            f.write("| " + " | ".join(["---"] * len(col_names)) + " |\n")
            for row in rows:
                f.write("| " + " | ".join([str(v) if v is not None else "NULL" for v in row]) + " |\n")
            f.write("\n")
        
        f.write("---\n\n")

print("Schema documentation generated successfully!")
