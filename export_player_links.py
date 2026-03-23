
import sqlite3, csv, os
db_path = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"
out_path = r"C:\AI\BillarLanzarote\data\raw_cuescore\review\player_cuescore_links.csv"
os.makedirs(os.path.dirname(out_path), exist_ok=True)
con = sqlite3.connect(db_path)
cur = con.cursor()
cur.execute("""
SELECT m.player_id, p.display_name, m.cuescore_player_id, m.cuescore_display_name, m.cuescore_profile_url, m.last_verified_ts_utc
FROM player_cuescore_map m
LEFT JOIN players p ON p.player_id = m.player_id
ORDER BY p.display_name
""")
rows = cur.fetchall()
con.close()
with open(out_path, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["player_id","display_name","cuescore_player_id","cuescore_display_name","cuescore_profile_url","last_verified_ts_utc"])
    w.writerows(rows)
print(out_path)
