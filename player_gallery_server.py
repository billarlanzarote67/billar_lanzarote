
import os, json, sqlite3
from flask import Flask, send_from_directory, jsonify, request

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
WEB = os.path.join(ROOT, "web_ui", "gallery")
LANG = os.path.join(ROOT, "config", "lang_es.json")
PHOTOS = os.path.join(ROOT, "data", "photos")

app = Flask(__name__, static_folder=WEB, static_url_path="")

def q(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def one(sql, params=()):
    rows = q(sql, params)
    return rows[0] if rows else None

@app.route("/")
def home():
    return send_from_directory(WEB, "index.html")

@app.route("/api/lang")
def api_lang():
    try:
        with open(LANG, "r", encoding="utf-8") as f:
            return jsonify(json.load(f))
    except Exception:
        return jsonify({})

@app.route("/api/players")
def api_players():
    rows = q("""
        SELECT p.name,
               COALESCE(COUNT(m.id),0) AS matches,
               COALESCE(SUM(CASE WHEN m.winner=p.name THEN 1 ELSE 0 END),0) AS wins,
               COALESCE(SUM(CASE WHEN m.winner IS NOT NULL AND m.winner<>p.name THEN 1 ELSE 0 END),0) AS losses,
               MAX(p.photo_url) AS photo_url
        FROM players p
        LEFT JOIN matches m ON m.player_a=p.name OR m.player_b=p.name
        GROUP BY p.name
        ORDER BY wins DESC, matches DESC, p.name
    """)
    out = []
    for r in rows:
        matches = r["matches"] or 0
        wins = r["wins"] or 0
        losses = r["losses"] or 0
        win_pct = round((wins / matches) * 100) if matches else 0
        out.append({
            "name": r["name"],
            "matches": matches,
            "wins": wins,
            "losses": losses,
            "win_pct": win_pct,
            "photo_url": r["photo_url"] or ""
        })
    return jsonify({"players": out})

@app.route("/photos/<path:name>")
def photos(name):
    return send_from_directory(PHOTOS, name)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8099, debug=False)
