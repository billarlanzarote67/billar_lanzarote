import sqlite3

db = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"

con = sqlite3.connect(db)
cur = con.cursor()

cur.execute("SELECT COUNT(*) FROM players")
count = cur.fetchone()[0]
print("players =", count)

cur.execute("SELECT display_name FROM players ORDER BY display_name LIMIT 20")
rows = cur.fetchall()

print("\nFirst players:")
for r in rows:
    print("-", r[0])

con.close()
