
import sqlite3, os
DB = r"C:\AI\BillarLanzarote\data\db\billar_lanzarote.db"
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS player_summary (
    name TEXT PRIMARY KEY,
    matches INTEGER,
    wins INTEGER,
    losses INTEGER,
    win_pct INTEGER
)
""")
cur.execute("DELETE FROM player_summary")
cur.execute("SELECT name FROM players ORDER BY name")
players = [r[0] for r in cur.fetchall()]
for name in players:
    cur.execute("SELECT COUNT(*) FROM matches WHERE player_a=? OR player_b=?", (name,name))
    matches = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM matches WHERE winner=?", (name,))
    wins = cur.fetchone()[0]
    losses = max(matches - wins, 0)
    win_pct = round((wins / matches) * 100) if matches else 0
    cur.execute("INSERT INTO player_summary(name,matches,wins,losses,win_pct) VALUES (?,?,?,?,?)", (name,matches,wins,losses,win_pct))
conn.commit(); conn.close()
print("player_summary rebuilt")
