import sqlite3

conn = sqlite3.connect('zozi.db')
cursor = conn.cursor()

# Check columns
cursor.execute("PRAGMA table_info(email_delivery_events)")
columns = [row[1] for row in cursor.fetchall()]
print("Columns:", columns)

# Check indexes
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='email_delivery_events'")
indexes = [row[0] for row in cursor.fetchall()]
print("Indexes:", indexes)

conn.close()
