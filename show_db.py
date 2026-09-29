import sqlite3
import os

db_path = os.path.join('database', 'instance', 'app.db')

if not os.path.exists(db_path):
    # fallback check
    db_path = os.path.join('instance', 'app.db')

if not os.path.exists(db_path):
    print("Database file not found!")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall() if not t[0].startswith('sqlite_')]

print("=" * 60)
print("          FARMER-TO-CONSUMER DATABASE OVERVIEW")
print("=" * 60)
print(f"Database File: {os.path.abspath(db_path)}\n")

for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM "{table}"')
    count = cursor.fetchone()[0]
    print(f"[+] Table: '{table}' ({count} rows)")
    
    cursor.execute(f'PRAGMA table_info("{table}");')
    columns = [col[1] for col in cursor.fetchall()]
    print(f"   Columns: {', '.join(columns)}")
    
    cursor.execute(f'SELECT * FROM "{table}" LIMIT 3;')
    rows = cursor.fetchall()
    if rows:
        print("   Sample Data:")
        for r in rows:
            safe_r = tuple(str(x).encode('ascii', 'replace').decode('ascii') if isinstance(x, str) else x for x in r)
            print(f"     - {safe_r}")
    else:
        print("   Sample Data: [No records yet]")
    print("-" * 60)

conn.close()
