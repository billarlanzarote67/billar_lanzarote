
import os, json, sqlite3
from flask import Flask, send_from_directory, jsonify, request

ROOT = r"C:\AI\BillarLanzarote"
DB = os.path.join(ROOT, "data", "db", "billar_lanzarote.db")
WEB = os.path.join(ROOT, "web_ui", "h2h")
LANG = os.path.join(ROOT, "config", "lang_es.json")
app = Flask(__name__, static_folder=WEB, static_url_path="")

def q(sql, params=()):
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

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
    rows = q("SELECT name FROM players ORDER BY name")
    return jsonify({"players":[r["name"] for r in rows]})

@app.route("/api/h2h")
def api_h2h():
    a = request.args.get("a", "")
    b = request.args.get("b", "")
    matches = q("""
        SELECT table_name, player_a, player_b, winner, score_a, score_b, timestamp
        FROM matches
        WHERE (player_a=? AND player_b=?) OR (player_a=? AND player_b=?)
        ORDER BY id DESC
    """, (a,b,b,a))
    wins_a = sum(1 for m in matches if m["winner"] == a)
    wins_b = sum(1 for m in matches if m["winner"] == b)
    return jsonify({
        "summary": {"matches": len(matches), "wins_a": wins_a, "wins_b": wins_b},
        "matches": matches
    })

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8791, debug=False)
