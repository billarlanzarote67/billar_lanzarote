import os
import sqlite3
from flask import Flask

DB_PRIMARY = r"C:\AI\BillarLanzarote\data\billar_lanzarote.sqlite3"
DB_FALLBACK = r"C:\AI\BillarLanzarote\database\sqlite\billar_lanzarote.sqlite"


def resolve_db() -> str:
    if os.path.exists(DB_PRIMARY):
        return DB_PRIMARY
    return DB_FALLBACK

DB = resolve_db()
app = Flask(__name__)


@app.route("/")
def index():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    try:
        cur.execute("SELECT COUNT(*) FROM players")
        player_count = cur.fetchone()[0]
    except Exception:
        player_count = 0
    try:
        stats = [dict(r) for r in cur.execute(
            """
            SELECT p.display_name,
                   s.matches_played,
                   s.wins,
                   s.losses,
                   s.win_rate,
                   s.frames_won,
                   s.frames_lost
            FROM players p
            LEFT JOIN player_profile_stats s ON s.player_id = p.player_id
            ORDER BY COALESCE(s.wins,0) DESC, p.display_name ASC
            LIMIT 300
            """
        ).fetchall()]
    except Exception:
        stats = []
    con.close()

    rows = ""
    for r in stats:
        def f(v):
            if v in (None, "", "None"):
                return ""
            try:
                return str(int(float(v)))
            except Exception:
                return str(v)
        wp = ""
        if r.get("win_rate") not in (None, "", "None"):
            try:
                wp = f"{round(float(r['win_rate']))}%"
            except Exception:
                wp = str(r.get("win_rate"))
        rows += (
            f"<tr><td>{r['display_name']}</td><td>{f(r.get('matches_played'))}</td>"
            f"<td>{f(r.get('wins'))}</td><td>{f(r.get('losses'))}</td>"
            f"<td>{f(r.get('frames_won'))}</td><td>{f(r.get('frames_lost'))}</td><td>{wp}</td></tr>"
        )

    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>Billar Lanzarote Admin Stats</title>
<style>
body{{font-family:Arial;background:#111;color:#eee;padding:20px}}
table{{width:100%;border-collapse:collapse}}
td,th{{border:1px solid #333;padding:8px}}
th{{background:#222}}
.muted{{color:#bbb}}
</style></head>
<body>
<h1>Billar Lanzarote Admin Stats</h1>
<div class='muted'>DB: {DB}</div>
<div class='muted'>Players in database: {player_count}</div>
<table>
<thead><tr><th>Player</th><th>Matches</th><th>Wins</th><th>Losses</th><th>Frames Won</th><th>Frames Lost</th><th>Win %</th></tr></thead>
<tbody>{rows}</tbody>
</table>
</body></html>"""


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8098, debug=False)
