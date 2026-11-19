import sqlite3
import json

con = sqlite3.connect(r"%USERPROFILE%\.codex\state_5.sqlite")
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print("Tables:", tables)

for table in tables:
    tname = table[0]
    try:
        cur.execute(f"SELECT * FROM {tname} LIMIT 5")
        rows = cur.fetchall()
        print(f"Table {tname}: {len(rows)} rows")
        # search for cloudflare or fenrir
        cur.execute(f"SELECT * FROM {tname}")
        for r in cur.fetchall():
            text = str(r)
            if "cloudflare" in text.lower() or "fenrir" in text.lower():
                print(f"Match in {tname}: {text[:300]}")
    except Exception as e:
        print(f"Error {tname}: {e}")

con.close()
