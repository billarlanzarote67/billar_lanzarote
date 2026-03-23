
import sqlite3, os
DB = r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT name FROM players ORDER BY name")
rows = cur.fetchall()
conn.close()
print("Players found:", len(rows))
for row in rows[:20]:
    print("-", row[0])
print("Profile refresh skeleton complete. Extend later with real profile parsing.")
