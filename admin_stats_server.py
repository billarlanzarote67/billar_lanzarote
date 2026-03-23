
import os, sqlite3
from flask import Flask, send_from_directory, jsonify

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
WEB = os.path.join(ROOT, "web_ui", "admin_stats")
app = Flask(__name__, static_folder=WEB, static_url_path="")

def q(sql):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

@app.route("/")
def home():
    return send_from_directory(WEB, "index.html")

@app.route("/api/stats")
def api_stats():
    rows = q("""
        SELECT p.name AS player,
               COALESCE(COUNT(m.id),0) AS matches,
               COALESCE(SUM(CASE WHEN m.winner=p.name THEN 1 ELSE 0 END),0) AS wins,
               COALESCE(SUM(CASE WHEN m.winner IS NOT NULL AND m.winner<>p.name THEN 1 ELSE 0 END),0) AS losses
        FROM players p
        LEFT JOIN matches m ON m.player_a=p.name OR m.player_b=p.name
        GROUP BY p.name
        ORDER BY wins DESC, matches DESC, p.name
    """)
    return jsonify({"rows": rows})

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8098, debug=False)
