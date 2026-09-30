import sqlite3, os

root = r'c:\Users\kv035\Downloads\Farmer-to-Consumer-App-main\Farmer-to-Consumer-App-main'
db_paths = [
    os.path.join(root, 'database', 'instance', 'app.db'),
    os.path.join(root, 'app.db')
]

for db_path in db_paths:
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(user)")
        cols = [row[1] for row in cur.fetchall()]
        print(f"Columns in {db_path}: {cols}")
        if 'preferred_language' in cols:
            try:
                cur.execute("ALTER TABLE user DROP COLUMN preferred_language")
                conn.commit()
                print(f"Successfully dropped column preferred_language from {db_path}")
            except Exception as e:
                print(f"Error dropping column from {db_path}: {e}")
        else:
            print(f"preferred_language column not found in {db_path}")
        conn.close()
